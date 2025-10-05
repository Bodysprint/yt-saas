#!/usr/bin/env python3
"""
Script de lancement pour transcription avec Playwright visible
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 50)
    print("  LANCEMENT TRANSCRIPTION AVEC PLAYWRIGHT")
    print("=" * 50)
    print()
    print("Le navigateur va s'ouvrir pour traiter les vidéos...")
    print()
    
    # Vérifier que urls.txt existe
    urls_file = Path("urls.txt")
    if not urls_file.exists():
        print("❌ Fichier urls.txt non trouvé")
        input("Appuyez sur Entrée pour fermer...")
        return
    
    urls = [line.strip() for line in urls_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    print(f"📝 {len(urls)} URL(s) à transcrire")
    print()
    
    try:
        # Lancer le script de transcription avec environnement visible
        result = subprocess.run(
            [sys.executable, "bot_yttotranscript.py"],
            cwd=Path.cwd(),
            env=os.environ.copy(),  # Copier l'environnement complet
            capture_output=False,   # Pas de capture pour permettre l'affichage
            text=True
        )
        
        print()
        print("=" * 50)
        if result.returncode == 0:
            print("✅ TRANSCRIPTION TERMINÉE AVEC SUCCÈS")
        else:
            print(f"❌ TRANSCRIPTION ÉCHOUÉE (code: {result.returncode})")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    input("Appuyez sur Entrée pour fermer...")

if __name__ == "__main__":
    main()

