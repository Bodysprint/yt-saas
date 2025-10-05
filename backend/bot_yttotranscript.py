"""
bot_yttotranscript.py
Automatisation Playwright pour récupérer des transcriptions via YouTubeToTranscript.com (ou youtube-transcript.com)
Place urls dans urls.txt (1 URL par ligne).
Les fichiers .txt seront sauvés dans ./transcripts/
"""

import time
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional

from rich import print
from rich.console import Console
from rich.panel import Panel

import yt_dlp

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

console = Console()
OUT_DIR = Path("transcripts")
OUT_DIR.mkdir(exist_ok=True)

URLS_FILE = Path("urls.txt")

# Sites à essayer dans l'ordre
TARGET_SITES = [
    "https://youtubetotranscript.com/",
    "https://youtube-transcript.com/",
    "https://youtubeto-transcript.com/",  # alternatives possibles
]

def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/*?:\"<>|\n\r\t]", "_", name)
    return re.sub(r"\s+", " ", name).strip()[:180]

def get_video_info(url: str) -> dict:
    """Récupère id + title via yt-dlp (rapide)"""
    ydl_opts = {"quiet": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {"id": info.get("id"), "title": info.get("title")}
    except Exception:
        # fallback to parse id
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        return {"id": vid or url, "title": url}

def save_txt(text: str, title: str, url: str):
    safe = sanitize_filename(title)
    out_path = OUT_DIR / f"{safe}.txt"
    header = f"{title}\n{url}\n\n"
    out_path.write_text(header + text, encoding="utf-8")
    return out_path

def try_extract_transcript_from_page(page) -> Optional[str]:
    """
    Essaye différents sélecteurs / heuristiques courants pour trouver le transcript sur la page.
    Retourne None si rien trouvé.
    """
    # 1) éléments avec id/class contenant "transcript"
    candidates = []
    selectors = [
        "[id*=transcript]", "[class*=transcript]", "pre", "textarea", ".result", ".output", ".trans", ".text"
    ]
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                txt = (el.inner_text() or "").strip()
                if len(txt) > 50:  # heuristique : au moins 50 chars
                    return txt
                elif len(txt) > 0:
                    candidates.append(txt)
        except Exception:
            continue

    # 2) chercher grands blocs de <div> visibles
    try:
        divs = page.query_selector_all("div")
        best = ""
        for d in divs:
            try:
                txt = (d.inner_text() or "").strip()
                if len(txt) > len(best):
                    best = txt
            except Exception:
                continue
        if len(best) > 50:
            return best
    except Exception:
        pass

    # fallback to any candidate > 0
    for c in candidates:
        if len(c) > 0:
            return c

    return None

def process_single_url(playwright, url: str, timeout_s: int = 30):  # Augmenté de 18 à 30 secondes
    info = get_video_info(url)
    title = info.get("title") or url
    console.print(Panel.fit(f"[bold]Video[/bold] : {title}", title="Traitement", border_style="cyan"))
    console.print(f"[blue]URL a traiter: {url}[/blue]")
    console.print("[green]Mode HEADLESS + STEALTH activé (navigateur invisible)[/green]")

    # Configuration Playwright en mode HEADLESS + STEALTH (invisible et anti-détection)
    browser = playwright.chromium.launch(
        headless=True,  # ← MODE INVISIBLE (aucune fenêtre)
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
        ]
    )
    
    # Contexte avec User-Agent réaliste
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='fr-FR',
        timezone_id='Europe/Paris'
    )
    
    page = context.new_page()
    
    # Appliquer les techniques de stealth pour contourner les détections anti-bot
    stealth_sync(page)
    
    # Techniques de stealth supplémentaires
    page.add_init_script("""
        // Masquer les propriétés d'automatisation
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Masquer les propriétés Playwright
        delete window.__playwright;
        delete window.__pw_manual;
        delete window.__pw_cleanup;
        
        // Simuler un navigateur normal
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['fr-FR', 'fr', 'en-US', 'en'],
        });
        
        // Masquer les traces d'automatisation
        window.chrome = {
            runtime: {},
        };
        
        // Simuler des permissions normales
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

    transcript_text = None

    for site in TARGET_SITES:
        try:
            console.print(f"- Ouverture {site}")
            page.goto(site, timeout=20000)
            console.print(f"[green]Page chargee: {site}[/green]")
            time.sleep(2)  # Augmenté de 0.8 à 2 secondes

            # 1) trouver input: on essaye quelques stratégies
            input_filled = False
            console.print(f"[blue]Recherche d'un champ d'entrée sur {site}...[/blue]")
            # Cherche input with placeholder contenant 'YouTube' ou 'video'
            inputs = page.query_selector_all("input, textarea")
            console.print(f"[blue]Trouve {len(inputs)} champs d'entree[/blue]")
            for inp in inputs:
                try:
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    typ = (inp.get_attribute("type") or "").lower()
                    name = (inp.get_attribute("name") or "").lower()
                    console.print(f"[blue]Champ: placeholder='{ph}', type='{typ}', name='{name}'[/blue]")
                    if "youtube" in ph or "video" in ph or "youtube" in name or "url" in name or typ in ("text", "search"):
                        # remplir et submit
                        console.print(f"[green]Champ trouve ! Remplissage avec: {url}[/green]")
                        inp.fill(url)
                        input_filled = True
                        break
                except Exception as e:
                    console.print(f"[yellow]Erreur avec un champ: {e}[/yellow]")
                    continue

            # si pas trouvé, remplir le premier input/textarea visible
            if not input_filled and inputs:
                try:
                    inputs[0].fill(url)
                    input_filled = True
                except Exception:
                    input_filled = False

            # Si toujours pas, essayer de coller via JS dans le premier input found by querySelector
            if not input_filled:
                try:
                    page.evaluate("() => { const i = document.querySelector('input, textarea'); if(i) i.value = ''; }")
                    page.evaluate(f"() => {{ const i = document.querySelector('input, textarea'); if(i) i.value = `{url}`; }}")
                    input_filled = True
                except Exception:
                    input_filled = False

            if not input_filled:
                console.print("[yellow]- Impossible de trouver un champ d'entrée sur ce site, j'essaie le suivant.[/yellow]")
                continue

            # 2) Soumettre : tenter Enter sur l'input ou cliquer sur un bouton 'Submit', 'Get Transcript', 'Go'
            console.print(f"[blue]Tentative de soumission...[/blue]")
            try:
                # try press Enter on focused element
                page.keyboard.press("Enter")
                console.print(f"[green]Entree pressee[/green]")
                time.sleep(2)  # Augmenté de 0.5 à 2 secondes
            except Exception as e:
                console.print(f"[yellow]Erreur avec Entrée: {e}[/yellow]")

            # try common button texts
            clicked = False
            btn_texts = ["Get Transcript", "Get transcript", "Get", "Submit", "Go", "Search", "Show transcript", "View Transcript", "Show"]
            console.print(f"[blue]Recherche de boutons: {btn_texts}[/blue]")
            for b in btn_texts:
                try:
                    btn = page.query_selector(f"button:has-text(\"{b}\")")
                    if btn:
                        console.print(f"[green]Bouton trouve: {b}[/green]")
                        btn.click()
                        clicked = True
                        break
                except Exception as e:
                    console.print(f"[yellow]Erreur avec bouton {b}: {e}[/yellow]")
                    continue

            # wait for result; we poll several seconds
            max_wait = timeout_s
            got = None
            since = 0
            console.print(f"[blue]Attente du resultat (max {max_wait}s)...[/blue]")
            while since < max_wait:
                time.sleep(1)  # Augmenté de 0.6 à 1 seconde
                since += 1
                console.print(f"[blue]Verification {since}/{max_wait}s...[/blue]")
                try:
                    txt = try_extract_transcript_from_page(page)
                    if txt and len(txt.strip()) > 30:
                        console.print(f"[green]Transcription trouvee ! Longueur: {len(txt)} caracteres[/green]")
                        got = txt
                        break
                    elif txt:
                        console.print(f"[yellow]Texte trouve mais trop court: {len(txt)} caracteres[/yellow]")
                except PlaywrightTimeoutError as e:
                    console.print(f"[yellow]Timeout: {e}[/yellow]")
                    pass

            if got:
                transcript_text = got
                console.print("[green]OK Transcription recuperee depuis le site.[/green]")
                break
            else:
                console.print(f"[yellow]- Pas de transcription detectee sur {site} (ou delai depasse). Je tente le site suivant.[/yellow]")
                continue

        except Exception as e:
            console.print(f"[red]- Erreur sur {site} : {e}[/red]")
            continue
        finally:
            # assure qu'on ferme l'onglet courant proprement
            try:
                context.clear_cookies()
            except Exception:
                pass

    # ferme navigateur
    try:
        browser.close()
    except Exception:
        pass

    if not transcript_text:
        console.print("[yellow]- Aucun transcript trouve via les sites testes pour cette video.[/yellow]")
        console.print("[blue]- Tentative avec l'API YouTube officielle...[/blue]")
        
        # Fallback: utiliser l'API YouTube officielle
        try:
            import yt_dlp
            import requests
            import re
            
            # Récupérer les sous-titres via yt-dlp
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["fr", "en"],
                "subtitlesformat": "vtt"
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", url)
                
                # Chercher des sous-titres disponibles
                subtitles = info.get("subtitles", {})
                auto_captions = info.get("automatic_captions", {})
                
                subtitle_url = None
                if "fr" in subtitles:
                    subtitle_url = subtitles["fr"][0]["url"]
                elif "en" in subtitles:
                    subtitle_url = subtitles["en"][0]["url"]
                elif "fr" in auto_captions:
                    subtitle_url = auto_captions["fr"][0]["url"]
                elif "en" in auto_captions:
                    subtitle_url = auto_captions["en"][0]["url"]
                
                if subtitle_url:
                    console.print("[green]- Sous-titre trouvé via API YouTube[/green]")
                    
                    # Télécharger le sous-titre avec délai et retry
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    # Délai avant la requête
                    import time
                    time.sleep(2)
                    
                    response = requests.get(subtitle_url, headers=headers, timeout=20)
                    
                    if response.status_code == 200:
                        vtt_content = response.text
                        
                        # Extraire le texte (format JSON)
                        try:
                            import json
                            data = json.loads(vtt_content)
                            text_parts = []
                            if 'events' in data:
                                for event in data['events']:
                                    if 'segs' in event:
                                        for seg in event['segs']:
                                            if 'utf8' in seg:
                                                text_parts.append(seg['utf8'])
                            
                            transcript_text = ' '.join(text_parts)
                            transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
                            
                            if transcript_text:
                                console.print("[green]- Transcription récupérée via API YouTube[/green]")
                            else:
                                console.print("[yellow]- Aucun texte extrait de l'API YouTube[/yellow]")
                        except:
                            # Fallback VTT classique
                            transcript_text = re.sub(r'<[^>]+>', '', vtt_content)
                            transcript_text = re.sub(r'^\d+$', '', transcript_text, flags=re.MULTILINE)
                            transcript_text = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$', '', transcript_text, flags=re.MULTILINE)
                            transcript_text = re.sub(r'^WEBVTT$', '', transcript_text, flags=re.MULTILINE)
                            transcript_text = re.sub(r'^\s*$', '', transcript_text, flags=re.MULTILINE)
                            transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
                    else:
                        console.print(f"[red]- Erreur API YouTube: {response.status_code}[/red]")
                else:
                    console.print("[yellow]- Aucun sous-titre disponible via API YouTube[/yellow]")
        except Exception as e:
            console.print(f"[red]- Erreur API YouTube: {e}[/red]")
        
        if not transcript_text:
            console.print("[red]- Aucun transcript trouvé via toutes les méthodes.[/red]\n")
            return

    # sauvegarde
    out_path = save_txt(transcript_text, title, url)
    console.print(f"[green]OK Enregistre :[/green] {out_path.resolve()}\n")

def main():
    if not URLS_FILE.exists():
        console.print("[red]Ajoute des URLs dans urls.txt (1 par ligne)[/red]")
        return

    urls = [ln.strip() for ln in URLS_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not urls:
        console.print("[red]Aucune URL trouvee dans urls.txt[/red]")
        return

    console.print(Panel.fit(f"Total videos : {len(urls)}", title="YT -> TXT via site externe"))

    with sync_playwright() as pw:
        for url in urls:
            process_single_url(pw, url)

    console.print(Panel.fit("Termine OK", border_style="green"))
    
    # Créer un fichier de signal de fin pour le frontend
    completion_file = Path("transcription_completed.txt")
    with open(completion_file, 'w', encoding='utf-8') as f:
        f.write(f"completed:{len(urls)}:{len(urls)}")
    console.print(f"[green]Signal de fin créé: {completion_file}[/green]")

if __name__ == "__main__":
    main()
