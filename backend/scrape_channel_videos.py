#!/usr/bin/env python3
"""
scrape_uploads.py
Scrape toutes les vidéos d'une chaîne (onglet /videos).
- Exclut les shorts
- Inclut vidéos + lives
- Sauvegarde dans urls.txt
"""

from pathlib import Path
import sys
import yt_dlp
import time

CHANNELS_FILE = Path("channels.txt")
OUT_FILE = Path("urls.txt")

def is_short(url: str) -> bool:
    return "/shorts/" in url

def scrape_uploads(url: str, limit: int | None = None):
    """
    Utilise yt-dlp pour extraire les vidéos de la playlist 'uploads' avec titres réels.
    Version optimisée : extraction rapide + enrichissement des titres en parallèle.
    """
    videos = []
    seen = set()

    # Phase 1: Extraction rapide avec extract_flat=True (comme avant)
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,  # RAPIDE - on veut juste les liens d'abord
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Si c'est un channel/@handle/videos, yt-dlp résout vers la playlist uploads
        entries = info.get("entries") or []
        count = 0
        for e in entries:
            if not e:
                continue

            video_id = e.get("id")
            webpage_url = e.get("url") or e.get("webpage_url")
            
            # Construire l'URL finale
            final_url = None
            if webpage_url and webpage_url.startswith("http"):
                final_url = webpage_url
            elif video_id:
                final_url = f"https://www.youtube.com/watch?v={video_id}"

            if not final_url:
                continue

            if is_short(final_url):
                continue

            if final_url in seen:
                continue

            seen.add(final_url)
            
            # Créer l'objet vidéo avec infos basiques d'abord (RAPIDE)
            video_data = {
                "url": final_url,
                "title": f"Vidéo {count + 1}",  # Titre temporaire
                "video_id": video_id,
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else None
            }
            videos.append(video_data)

            count += 1
            if limit and count >= limit:
                break

    # Phase 2: Enrichissement des titres en parallèle (sans bloquer)
    print(f"[+] Enrichissement des titres pour {len(videos)} vidéos...")
    
    # Sauvegarder d'abord avec les titres temporaires pour l'affichage instantané
    save_videos_to_file(videos)
    
    for i, video in enumerate(videos):
        try:
            # Extraction rapide du titre depuis la page YouTube
            title = get_video_title_fast(video["video_id"])
            if title:
                video["title"] = title
                print(f"   [{i+1}/{len(videos)}] {title[:50]}...")
            else:
                print(f"   [{i+1}/{len(videos)}] Titre non trouvé, garde le titre temporaire")
        except Exception as e:
            print(f"   [{i+1}/{len(videos)}] Erreur enrichissement: {e}")
            # Garde le titre temporaire en cas d'erreur
        
        # Sauvegarder après chaque enrichissement pour mise à jour en temps réel
        save_videos_to_file(videos)

    # Enrichissement terminé
    print(f"[✓] Enrichissement terminé pour {len(videos)} vidéos")

    return videos

def save_videos_to_file(videos):
    """Sauvegarde les vidéos dans urls.txt en JSON"""
    import json
    try:
        OUT_FILE.write_text(json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")

def create_completion_signal(video_count):
    """Crée un signal de fin de scraping pour que le backend sache que c'est terminé"""
    try:
        completion_file = Path("scraping_completed.txt")
        completion_file.write_text(f"completed:{video_count}", encoding="utf-8")
        print(f"[✓] Signal de fin créé: {video_count} vidéos")
    except Exception as e:
        print(f"Erreur création signal: {e}")

def get_video_title_fast(video_id):
    """Récupère rapidement le titre d'une vidéo YouTube"""
    try:
        import requests
        import re
        
        if not video_id:
            return None
            
        # Utiliser l'API publique de YouTube (sans clé API)
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, timeout=3)  # Timeout court pour la rapidité
        
        if response.status_code == 200:
            # Extraire le titre depuis la page HTML
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                title = title_match.group(1)
                # Nettoyer le titre (enlever " - YouTube")
                title = title.replace(' - YouTube', '').strip()
                return title
    except Exception as e:
        print(f"Erreur récupération titre {video_id}: {e}")
    
    return None

def main():
    if len(sys.argv) >= 2:
        channels = [sys.argv[1].strip()]
        limit = int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else None
    else:
        if not CHANNELS_FILE.exists():
            print("-> Ajoute l'URL /videos dans channels.txt OU passe-la en argument.")
            return
        channels = [ln.strip() for ln in CHANNELS_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
        limit = None

    all_videos = []
    seen = set()

    for ch in channels:
        print(f"[+] Scraping : {ch}")
        try:
            found = scrape_uploads(ch, limit)
            print(f"   -> {len(found)} videos trouvees")
        except Exception as e:
            print(f"   ! Erreur : {e}")
            found = []

        for video in found:
            if video["url"] not in seen:
                seen.add(video["url"])
                all_videos.append(video)

        time.sleep(1.0)

    if all_videos:
        # Les vidéos ont déjà été sauvegardées progressivement
        print(f"[OK] {len(all_videos)} video(s) avec titres reels ecrites dans {OUT_FILE.resolve()}")
        # Créer le signal de fin final
        create_completion_signal(len(all_videos))
        print("[✓] Scraping et enrichissement complètement terminés")
    else:
        print("[!] Aucune video trouvee.")
        # Créer un signal de fin même si aucune vidéo
        create_completion_signal(0)

if __name__ == "__main__":
    main()
