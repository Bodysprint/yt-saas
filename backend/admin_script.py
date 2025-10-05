#!/usr/bin/env python3
"""
Script d'administration pour YouTube Transcript App
Permet de gérer les utilisateurs via ligne de commande
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
ADMIN_KEY = os.getenv('ADMIN_KEY', 'dev-admin-key')

def make_admin_request(endpoint, method='GET', data=None):
    """Fait une requête à l'API admin"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        'X-Admin-Key': ADMIN_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"Méthode {method} non supportée")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return None

def list_users():
    """Liste tous les utilisateurs"""
    print("📋 Liste des utilisateurs:")
    result = make_admin_request('/api/admin/users')
    if result:
        users = result.get('users', [])
        if not users:
            print("Aucun utilisateur trouvé")
            return
        
        print(f"Total: {len(users)} utilisateur(s)")
        print("-" * 80)
        for user in users:
            premium_status = "✅ Premium" if user['premium'] else "❌ Standard"
            print(f"📧 {user['email']}")
            print(f"   {premium_status} | Essais: {user['trial_count']}")
            print(f"   Créé: {user['created_at']}")
            print()

def set_premium(email, premium=True):
    """Active/désactive le statut premium d'un utilisateur"""
    data = {'email': email, 'premium': premium}
    result = make_admin_request('/api/admin/set-premium', 'POST', data)
    if result:
        status = "activé" if premium else "désactivé"
        print(f"✅ Statut premium {status} pour {email}")

def reset_trial(email):
    """Remet à zéro le compteur d'essais d'un utilisateur"""
    data = {'email': email}
    result = make_admin_request('/api/admin/reset-trial', 'POST', data)
    if result:
        print(f"✅ Compteur d'essais remis à zéro pour {email}")

def show_help():
    """Affiche l'aide"""
    print("""
🔧 Script d'administration - YouTube Transcript App

Usage:
    python admin_script.py <commande> [arguments]

Commandes disponibles:
    list                    - Liste tous les utilisateurs
    premium <email> <true/false> - Active/désactive le premium
    reset <email>           - Remet à zéro les essais
    help                    - Affiche cette aide

Exemples:
    python admin_script.py list
    python admin_script.py premium user@example.com true
    python admin_script.py reset user@example.com

Variables d'environnement:
    API_BASE_URL - URL de l'API (défaut: http://127.0.0.1:8000)
    ADMIN_KEY - Clé d'administration
    """)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_users()
    
    elif command == 'premium':
        if len(sys.argv) < 4:
            print("❌ Usage: python admin_script.py premium <email> <true/false>")
            return
        email = sys.argv[2]
        premium = sys.argv[3].lower() == 'true'
        set_premium(email, premium)
    
    elif command == 'reset':
        if len(sys.argv) < 3:
            print("❌ Usage: python admin_script.py reset <email>")
            return
        email = sys.argv[2]
        reset_trial(email)
    
    elif command == 'help':
        show_help()
    
    else:
        print(f"❌ Commande inconnue: {command}")
        show_help()

if __name__ == "__main__":
    main()
