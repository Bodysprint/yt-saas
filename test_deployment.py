#!/usr/bin/env python3
"""
Script de test pour valider le déploiement
"""

import requests
import json
import sys
from pathlib import Path

def test_backend_health():
    """Test de l'endpoint de santé du backend"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("Backend Health Check: OK")
                return True
            else:
                print(f"Backend Health Check: Reponse inattendue {data}")
                return False
        else:
            print(f"Backend Health Check: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Backend Health Check: Erreur de connexion - {e}")
        return False

def test_frontend_build():
    """Test que le build du frontend fonctionne"""
    try:
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("Frontend Build: Dossier frontend non trouve")
            return False
        
        dist_dir = frontend_dir / "dist"
        if not dist_dir.exists():
            print("Frontend Build: Dossier dist non trouve - build necessaire")
            return False
        
        index_file = dist_dir / "index.html"
        if not index_file.exists():
            print("Frontend Build: index.html non trouve")
            return False
        
        print("Frontend Build: OK")
        return True
    except Exception as e:
        print(f"Frontend Build: Erreur - {e}")
        return False

def test_config_files():
    """Test que les fichiers de configuration sont présents"""
    config_files = [
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/env.example",
        "render.yaml",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    missing_files = []
    for file_path in config_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Configuration: Fichiers manquants - {missing_files}")
        return False
    else:
        print("Configuration: Tous les fichiers presents")
        return True

def test_api_structure():
    """Test que la structure API est correcte"""
    try:
        api_file = Path("frontend/src/api.js")
        if not api_file.exists():
            print("API Structure: api.js non trouve")
            return False
        
        config_file = Path("frontend/src/config.js")
        if not config_file.exists():
            print("API Structure: config.js non trouve")
            return False
        
        # Verifier que config.js utilise VITE_API_URL
        config_content = config_file.read_text(encoding='utf-8')
        if "VITE_API_URL" not in config_content:
            print("API Structure: VITE_API_URL non utilise dans config.js")
            return False
        
        print("API Structure: OK")
        return True
    except Exception as e:
        print(f"API Structure: Erreur - {e}")
        return False

def main():
    """Fonction principale de test"""
    print("TEST DE DEPLOIEMENT - YouTube Transcript SaaS")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_config_files),
        ("Structure API", test_api_structure),
        ("Build Frontend", test_frontend_build),
        ("Backend Health", test_backend_health),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("RESULTATS FINAUX")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("DEPLOIEMENT PRET !")
        print("Tous les tests sont passes")
        print("Pret pour le deploiement sur Render")
        print("\nProchaines etapes :")
        print("1. Pousser le code sur GitHub")
        print("2. Creer les services sur Render")
        print("3. Configurer les variables d'environnement")
        print("4. Activer l'auto-deploy")
        return 0
    else:
        print("DEPLOIEMENT NON PRET")
        print("Corriger les erreurs avant de deployer")
        return 1

if __name__ == "__main__":
    sys.exit(main())
