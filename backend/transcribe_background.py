#!/usr/bin/env python3
"""
Script de transcription en arrière-plan
Lance le bot original avec navigateur visible pour debug
"""

import time
import subprocess
import sys
from pathlib import Path

def main():
    print("=== Transcription avec navigateur visible ===")
    
    # Vérifier que urls.txt existe
    urls_file = Path("urls.txt")
    if not urls_file.exists():
        print("❌ Fichier urls.txt non trouvé")
        return False
    
    urls = [line.strip() for line in urls_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    print(f"📝 {len(urls)} URL(s) à transcrire")
    
    # Lancer le script de transcription original avec navigateur visible
    try:
        print("🚀 Lancement du bot de transcription (navigateur visible)...")
        print("   Le navigateur va s'ouvrir - c'est normal pour le debug")
        
        # D'abord, tester les dépendances
        print("🔍 Vérification des dépendances...")
        try:
            import playwright
            print("   ✅ Playwright importé")
        except ImportError as e:
            print(f"   ❌ Playwright non installé: {e}")
            return False
            
        try:
            import rich
            print("   ✅ Rich importé")
        except ImportError as e:
            print(f"   ❌ Rich non installé: {e}")
            return False
            
        try:
            import yt_dlp
            print("   ✅ yt-dlp importé")
        except ImportError as e:
            print(f"   ❌ yt-dlp non installé: {e}")
            return False
        
        # Utiliser subprocess.run pour capturer les erreurs
        print("🚀 Lancement du bot de transcription...")
        result = subprocess.run(
            [sys.executable, "bot_yttotranscript.py"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        print(f"Code de retour: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Transcription terminée avec succès")
            return True
        else:
            print(f"❌ Erreur de transcription (code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
