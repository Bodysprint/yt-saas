#!/usr/bin/env python3
"""
Script de test simple pour vérifier si bot_yttotranscript.py fonctionne
"""

import subprocess
import sys
from pathlib import Path

def test_bot():
    print("=== Test du bot de transcription ===")
    
    # Vérifier que le fichier urls.txt existe
    urls_file = Path("urls.txt")
    if not urls_file.exists():
        print("❌ Fichier urls.txt non trouvé")
        return False
    
    print(f"✅ Fichier urls.txt trouvé")
    print(f"Contenu: {urls_file.read_text(encoding='utf-8')}")
    
    # Vérifier que le script bot existe
    bot_script = Path("bot_yttotranscript.py")
    if not bot_script.exists():
        print("❌ Script bot_yttotranscript.py non trouvé")
        return False
    
    print("✅ Script bot_yttotranscript.py trouvé")
    
    # Tester l'import des dépendances
    try:
        import playwright
        print("✅ Playwright importé")
    except ImportError as e:
        print(f"❌ Erreur import Playwright: {e}")
        return False
    
    try:
        import rich
        print("✅ Rich importé")
    except ImportError as e:
        print(f"❌ Erreur import Rich: {e}")
        return False
    
    try:
        import yt_dlp
        print("✅ yt-dlp importé")
    except ImportError as e:
        print(f"❌ Erreur import yt-dlp: {e}")
        return False
    
    # Tester l'exécution du script
    print("\n=== Lancement du script ===")
    try:
        result = subprocess.run(
            [sys.executable, "bot_yttotranscript.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Code de retour: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Script exécuté avec succès")
            return True
        else:
            print("❌ Script a échoué")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout - le script prend trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")
        return False

if __name__ == "__main__":
    success = test_bot()
    sys.exit(0 if success else 1)
