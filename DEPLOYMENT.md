# 🚀 Guide de Déploiement - YouTube Transcript App

Ce guide explique comment déployer l'application YouTube Transcript App sur Render (backend) et Netlify (frontend).

## 📋 Prérequis

1. **Compte Supabase** - Base de données PostgreSQL
2. **Compte Render** - Hébergement backend
3. **Compte Netlify** - Hébergement frontend
4. **Compte GitHub** - Repository du code

## 🗄️ Étape 1 : Configuration Supabase

### 1.1 Créer un projet Supabase
1. Aller sur [supabase.com](https://supabase.com)
2. Créer un nouveau projet
3. Noter l'URL de connexion et les credentials

### 1.2 Exécuter le schéma SQL
1. Aller dans l'éditeur SQL de Supabase
2. Exécuter le contenu du fichier `backend/supabase_schema.sql`
3. Vérifier que la table `users` est créée

### 1.3 Récupérer la DATABASE_URL
1. Aller dans Settings > Database
2. Copier la "Connection string" (URI)
3. Format : `postgresql://username:password@host:port/database`

## 🔧 Étape 2 : Déploiement Backend (Render)

### 2.1 Préparer le repository
1. Pousser le code sur GitHub
2. S'assurer que tous les fichiers sont présents :
   - `backend/Procfile`
   - `backend/requirements.txt`
   - `backend/app.py` (modifié)
   - `backend/supabase_schema.sql`

### 2.2 Créer un service sur Render
1. Aller sur [render.com](https://render.com)
2. Créer un nouveau "Web Service"
3. Connecter le repository GitHub
4. Configuration :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment** : Python 3

### 2.3 Variables d'environnement Render
Ajouter ces variables dans Render :
```
DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your-secret-key-here
TRIAL_LIMIT=3
ADMIN_KEY=your-admin-key-here
FLASK_ENV=production
FLASK_DEBUG=False
```

### 2.4 Déployer
1. Cliquer sur "Deploy"
2. Attendre la fin du déploiement
3. Noter l'URL du service (ex: `https://your-app.onrender.com`)

## 🌐 Étape 3 : Déploiement Frontend (Netlify)

### 3.1 Préparer le repository
S'assurer que le frontend contient :
- `frontend/netlify.toml`
- `frontend/vite.config.js` (modifié)
- `frontend/src/config.js` (modifié)

### 3.2 Créer un site sur Netlify
1. Aller sur [netlify.com](https://netlify.com)
2. Créer un nouveau site depuis Git
3. Connecter le repository GitHub
4. Configuration :
   - **Base directory** : `frontend`
   - **Build command** : `npm run build`
   - **Publish directory** : `frontend/dist`

### 3.3 Variables d'environnement Netlify
Ajouter dans Site settings > Environment variables :
```
VITE_API_URL=https://your-backend-app.onrender.com
```

### 3.4 Déployer
1. Cliquer sur "Deploy site"
2. Attendre la fin du déploiement
3. Noter l'URL du site (ex: `https://your-app.netlify.app`)

## 🔒 Étape 4 : Configuration CORS

### 4.1 Mettre à jour le backend
Modifier `backend/app.py` pour autoriser l'URL Netlify :
```python
CORS(app, resources={r"/api/*": {
    "origins": [
        "http://127.0.0.1:5173", 
        "http://localhost:5173",
        "https://your-app.netlify.app"  # Ajouter cette ligne
    ]
}}, supports_credentials=True)
```

### 4.2 Redéployer le backend
1. Commiter les changements
2. Render redéploiera automatiquement

## 👨‍💼 Étape 5 : Gestion des utilisateurs

### 5.1 Endpoints d'administration
Utiliser ces endpoints pour gérer les utilisateurs :

**Activer un compte premium :**
```bash
curl -X POST https://your-backend-app.onrender.com/api/admin/set-premium \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{"email": "user@example.com", "premium": true}'
```

**Lister tous les utilisateurs :**
```bash
curl -X GET https://your-backend-app.onrender.com/api/admin/users \
  -H "X-Admin-Key: your-admin-key"
```

**Remettre à zéro les essais :**
```bash
curl -X POST https://your-backend-app.onrender.com/api/admin/reset-trial \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{"email": "user@example.com"}'
```

## 🧪 Étape 6 : Tests

### 6.1 Test d'inscription
1. Aller sur l'URL Netlify
2. Créer un compte
3. Vérifier dans Supabase que l'utilisateur est créé

### 6.2 Test de transcription
1. Se connecter
2. Essayer de transcrire une vidéo
3. Vérifier que le compteur d'essais s'incrémente

### 6.3 Test des limites
1. Utiliser 3 essais
2. Vérifier que la transcription est bloquée
3. Activer le premium via l'API admin
4. Vérifier que la transcription fonctionne à nouveau

## 🔧 Maintenance

### Logs
- **Render** : Voir les logs dans le dashboard Render
- **Netlify** : Voir les logs dans le dashboard Netlify
- **Supabase** : Voir les logs dans le dashboard Supabase

### Sauvegarde
- **Base de données** : Supabase fait des sauvegardes automatiques
- **Code** : Sauvegardé sur GitHub

### Mise à jour
1. Modifier le code localement
2. Commiter et pousser sur GitHub
3. Render et Netlify redéploieront automatiquement

## 🚨 Dépannage

### Problèmes courants

**Erreur CORS :**
- Vérifier que l'URL Netlify est dans la liste CORS du backend

**Erreur de base de données :**
- Vérifier la DATABASE_URL dans Render
- Vérifier que la table `users` existe dans Supabase

**Erreur de build :**
- Vérifier les variables d'environnement
- Vérifier les dépendances dans requirements.txt

**Playwright ne fonctionne pas :**
- Render ne supporte pas Playwright par défaut
- Considérer utiliser un service externe pour la transcription

## 📞 Support

En cas de problème :
1. Vérifier les logs dans les dashboards
2. Tester les endpoints avec curl
3. Vérifier la configuration des variables d'environnement
