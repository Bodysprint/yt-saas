# YT-SaaS - Transcription YouTube

Application de transcription de vidéos YouTube avec interface web moderne et système de gestion des utilisateurs.

## 🌟 Nouvelles fonctionnalités

- ✅ **Système d'authentification** : Inscription/Connexion avec base de données
- ✅ **Essais limités** : 3 essais gratuits par utilisateur
- ✅ **Comptes premium** : Accès illimité pour les utilisateurs premium
- ✅ **Administration** : Gestion des utilisateurs via API admin
- ✅ **Déploiement cloud** : Prêt pour Render (backend) et Netlify (frontend)
- ✅ **Base de données Supabase** : PostgreSQL hébergé

## 🚀 Démarrage rapide

### 1. Installation des dépendances

```bash
# Backend (Python)
cd backend
pip install -r requirements.txt
playwright install chromium

# Frontend (Node.js)
cd frontend
npm install
```

### 2. Lancement de l'application

```bash
# À la racine du projet
start.bat
```

Cela lance automatiquement :
- Backend Flask sur http://127.0.0.1:8000
- Frontend Vite sur http://127.0.0.1:5173

### 3. Utilisation

1. **Inscription/Connexion** : Créez un compte ou connectez-vous
2. **Scraper une chaîne** : Entrez l'URL d'une chaîne YouTube (ex: `https://www.youtube.com/@markbuildsbrands/videos`)
3. **Sélectionner des vidéos** : Cochez les vidéos à transcrire
4. **Transcrire** : 
   - "Transcrire sélectionnées" : pour les vidéos cochées
   - "Transcrire tout" : pour toutes les vidéos scrapées
5. **Consulter les résultats** : Les fichiers .txt apparaissent dans la liste

## 🔧 Fonctionnalités

### Core
- ✅ **Scraping de chaînes YouTube** : Récupère toutes les vidéos d'une chaîne
- ✅ **Transcription automatique** : Utilise Playwright + sites de transcription
- ✅ **Interface moderne** : React + Tailwind CSS
- ✅ **Téléchargement** : Export des transcriptions en ZIP
- ✅ **Logs en temps réel** : Suivi des opérations

### Authentification & Gestion
- ✅ **Système d'utilisateurs** : Base de données PostgreSQL (Supabase)
- ✅ **Essais limités** : 3 transcriptions gratuites par utilisateur
- ✅ **Comptes premium** : Accès illimité
- ✅ **API d'administration** : Gestion des utilisateurs
- ✅ **Sécurité** : Authentification par clé admin

## 📁 Structure

```
yt-saas-final/
├── backend/                 # Scripts Python + Flask
│   ├── bot_yttotranscript.py    # Script principal de transcription
│   ├── scrape_channel_videos.py # Script de scraping
│   ├── lancer_bot (2).bat       # Lanceur Windows (.bat)
│   ├── app.py                   # API Flask (avec SQLAlchemy)
│   ├── admin_script.py          # Script d'administration
│   ├── Procfile                 # Configuration Render
│   ├── requirements.txt         # Dépendances Python
│   ├── supabase_schema.sql      # Schéma base de données
│   ├── transcripts/             # Fichiers .txt générés
│   └── urls.txt                 # URLs à transcrire
├── frontend/               # Interface React
│   ├── src/
│   │   ├── pages/Dashboard.jsx  # Page principale
│   │   ├── components/          # Composants React
│   │   └── config.js            # Configuration API
│   ├── netlify.toml             # Configuration Netlify
│   └── vite.config.js           # Configuration Vite
├── DEPLOYMENT.md           # Guide de déploiement
└── start.bat              # Lanceur principal
```

## 🛠️ Dépannage

### Problème : "Script de transcription non trouvé"
- Vérifiez que `backend/lancer_bot (2).bat` existe
- Le nom du fichier doit contenir l'espace et les parenthèses

### Problème : "Playwright non installé"
```bash
cd backend
playwright install chromium
```

### Problème : Aucune transcription générée
1. Vérifiez que `urls.txt` contient des URLs
2. Testez manuellement : double-cliquez sur `lancer_bot (2).bat`
3. Vérifiez les logs dans l'interface

### Problème : CORS
- Backend : http://127.0.0.1:8000
- Frontend : http://127.0.0.1:5173
- Ne pas utiliser localhost

## 👨‍💼 Gestion des utilisateurs

### Script d'administration
```bash
# Lister tous les utilisateurs
python backend/admin_script.py list

# Activer le premium pour un utilisateur
python backend/admin_script.py premium user@example.com true

# Remettre à zéro les essais
python backend/admin_script.py reset user@example.com
```

### API d'administration
```bash
# Activer le premium
curl -X POST https://your-app.onrender.com/api/admin/set-premium \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "premium": true}'

# Lister les utilisateurs
curl -X GET https://your-app.onrender.com/api/admin/users \
  -H "X-Admin-Key: your-admin-key"
```

## 📝 Notes techniques

- **Backend** : Flask WSGI avec SQLAlchemy
- **Base de données** : PostgreSQL (Supabase)
- **Transcription** : Playwright + sites externes (pas d'API YouTube)
- **Déploiement** : Render (backend) + Netlify (frontend)
- **Authentification** : Système de tokens simple

## 🎯 Flux de travail

1. **Scraping** : `scrape_channel_videos.py` → `urls.txt`
2. **Transcription** : `bot_yttotranscript.py` → `transcripts/*.txt`
3. **Interface** : Dashboard → API Flask → Scripts Python
4. **Résultat** : Fichiers .txt dans `backend/transcripts/`
