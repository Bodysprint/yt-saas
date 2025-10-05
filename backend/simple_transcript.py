#!/usr/bin/env python3
"""
Script de transcription simplifié utilisant l'API YouTube officielle
"""

import os
import sys
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Ajouter le répertoire courant au path pour importer yt_dlp
sys.path.insert(0, str(Path(__file__).parent))

try:
    import yt_dlp
except ImportError:
    print("Erreur: yt-dlp non installé. Installez avec: pip install yt-dlp")
    sys.exit(1)

OUT_DIR = Path("transcripts")
OUT_DIR.mkdir(exist_ok=True)

URLS_FILE = Path("urls.txt")

def get_video_id(url):
    """Extrait l'ID vidéo depuis l'URL YouTube"""
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id_match.group(1) if video_id_match else None

def get_video_info(url):
    """Récupère les infos vidéo via yt-dlp"""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["fr", "en"],
        "subtitlesformat": "vtt"
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "subtitles": info.get("subtitles", {}),
                "automatic_captions": info.get("automatic_captions", {})
            }
    except Exception as e:
        print(f"Erreur yt-dlp: {e}")
        return None

def download_subtitle(subtitle_url, video_title, video_url):
    """Télécharge et convertit un sous-titre en format texte propre"""
    try:
        import requests
        from logger import logger
        
        logger.log_transcription(video_url, "TÉLÉCHARGEMENT", f"URL: {subtitle_url}")
        
        # Headers pour éviter les blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(subtitle_url, timeout=15, headers=headers)
        if response.status_code == 200:
            vtt_content = response.text
            logger.log_transcription(video_url, "VTT_RÉCUPÉRÉ", f"Taille: {len(vtt_content)} caractères")
            
            # Extraire seulement le texte des sous-titres (format JSON)
            try:
                import json
                data = json.loads(vtt_content)
                
                # Extraire le texte des segments
                text_parts = []
                if 'events' in data:
                    for event in data['events']:
                        if 'segs' in event:
                            for seg in event['segs']:
                                if 'utf8' in seg:
                                    text_parts.append(seg['utf8'])
                
                # Joindre et nettoyer le texte
                clean_text = ' '.join(text_parts)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                logger.log_transcription(video_url, "TEXTE_EXTRAIT", f"Longueur: {len(clean_text)} caractères")
                
            except json.JSONDecodeError:
                # Fallback: traitement VTT classique
                logger.log_warning(f"Format VTT détecté pour {video_url}, conversion...")
                clean_text = re.sub(r'<[^>]+>', '', vtt_content)
                clean_text = re.sub(r'^\d+$', '', clean_text, flags=re.MULTILINE)
                clean_text = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$', '', clean_text, flags=re.MULTILINE)
                clean_text = re.sub(r'^WEBVTT$', '', clean_text, flags=re.MULTILINE)
                clean_text = re.sub(r'^\s*$', '', clean_text, flags=re.MULTILINE)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if not clean_text:
                logger.log_error(f"Aucun texte extrait pour {video_url}")
                return None
            
            # Nettoyer le titre pour le nom de fichier
            safe_title = re.sub(r'[\\/*?:"<>|]', '_', video_title)
            safe_title = safe_title[:100]  # Limiter la longueur
            
            # Sauvegarder en format propre
            file_path = OUT_DIR / f"{safe_title}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"TITRE: {video_title}\n")
                f.write(f"URL: {video_url}\n")
                f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(clean_text)
            
            logger.log_transcription(video_url, "SAUVEGARDÉ", f"Fichier: {file_path}")
            return file_path
        else:
            logger.log_error(f"Erreur HTTP {response.status_code} pour {video_url}")
            return None
            
    except Exception as e:
        logger.log_error(f"Erreur téléchargement sous-titre: {e}")
    
    return None

def process_video(url):
    """Traite une vidéo pour extraire sa transcription"""
    print(f"Traitement: {url}")
    
    video_id = get_video_id(url)
    if not video_id:
        print(f"  ❌ Impossible d'extraire l'ID vidéo de: {url}")
        return False
    
    # Récupérer les infos vidéo
    info = get_video_info(url)
    if not info:
        print(f"  ❌ Impossible de récupérer les infos vidéo")
        return False
    
    title = info.get("title", f"Vidéo {video_id}")
    print(f"  📺 Titre: {title}")
    
    # Chercher des sous-titres disponibles
    subtitles = info.get("subtitles", {})
    auto_captions = info.get("automatic_captions", {})
    
    # Priorité: sous-titres manuels français, puis anglais, puis auto-captions
    subtitle_url = None
    lang = None
    
    if "fr" in subtitles:
        subtitle_url = subtitles["fr"][0]["url"]
        lang = "français"
    elif "en" in subtitles:
        subtitle_url = subtitles["en"][0]["url"]
        lang = "anglais"
    elif "fr" in auto_captions:
        subtitle_url = auto_captions["fr"][0]["url"]
        lang = "français (auto)"
    elif "en" in auto_captions:
        subtitle_url = auto_captions["en"][0]["url"]
        lang = "anglais (auto)"
    
    if not subtitle_url:
        print(f"  ❌ Aucun sous-titre disponible")
        return False
    
    print(f"  📝 Sous-titre trouvé ({lang})")
    
    # Télécharger et sauvegarder
    file_path = download_subtitle(subtitle_url, title, url)
    if file_path:
        print(f"  ✅ Sauvegardé: {file_path}")
        return True
    else:
        print(f"  ❌ Échec du téléchargement")
        return False

def main():
    from logger import logger
    
    logger.log_info("Démarrage du script de transcription")
    
    if not URLS_FILE.exists():
        logger.log_error("Fichier urls.txt non trouvé")
        return
    
    urls = [line.strip() for line in URLS_FILE.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not urls:
        logger.log_error("Aucune URL trouvée dans urls.txt")
        return
    
    logger.log_info(f"Traitement de {len(urls)} vidéo(s)")
    print(f"🎬 Traitement de {len(urls)} vidéo(s)")
    
    success_count = 0
    for i, url in enumerate(urls, 1):
        logger.log_transcription(url, "DÉBUT", f"Vidéo {i}/{len(urls)}")
        print(f"\n[{i}/{len(urls)}] {url}")
        if process_video(url):
            success_count += 1
            logger.log_transcription(url, "SUCCÈS", "Transcription terminée")
        else:
            logger.log_transcription(url, "ÉCHEC", "Transcription échouée")
    
    logger.log_success(f"Terminé: {success_count}/{len(urls)} vidéos transcrites")
    print(f"\n✅ Terminé: {success_count}/{len(urls)} vidéos transcrites")
    
    # Créer un fichier de signal de fin pour le frontend
    completion_file = Path("transcription_completed.txt")
    with open(completion_file, 'w', encoding='utf-8') as f:
        f.write(f"completed:{success_count}:{len(urls)}")
    logger.log_info(f"Signal de fin créé: {completion_file}")

if __name__ == "__main__":
    main()
