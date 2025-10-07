# Guide de Déploiement Render

## 🚀 Déploiement Automatique

Ce projet est configuré pour un déploiement automatique sur Render avec synchronisation GitHub.

### 📋 Prérequis

1. **Compte Render** : Créez un compte sur [render.com](https://render.com)
2. **Repository GitHub** : Le code doit être poussé sur GitHub
3. **Base de données Supabase** : Configuration PostgreSQL déjà en place

### 🔧 Configuration Backend (Web Service)

1. **Type de service** : Web Service
2. **Environnement** : Python 3.13
3. **Build Command** : `pip install -r requirements.txt`
4. **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT`

#### Variables d'environnement Backend :
```
DATABASE_URL=postgresql://postgres:<password>@db.oefpxwciddvgqvpnyhnu.supabase.co:5432/postgres
ADMIN_KEY=admin-key-1234
SECRET_KEY=secret-key-render-2024
TRIAL_LIMIT=10
FLASK_ENV=production
FLASK_DEBUG=False
```

### 🎨 Configuration Frontend (Static Site)

1. **Type de service** : Static Site
2. **Build Command** : `npm install && npm run build`
3. **Publish Directory** : `dist`

#### Variables d'environnement Frontend :
```
VITE_API_URL=https://yt-saas-backend.onrender.com
```

### 🔄 Synchronisation GitHub

1. **Auto Deploy** : Activé sur la branche `main`
2. **Chaque push** déclenche :
   - Rebuild du backend
   - Rebuild du frontend
   - Synchronisation des variables d'environnement

### 🧪 Tests de Validation

#### Test Backend :
```bash
curl https://yt-saas-backend.onrender.com/api/health
# Réponse attendue : {"status": "ok"}
```

#### Test Frontend :
1. Ouvrir https://yt-saas-frontend.onrender.com
2. Vérifier dans F12 → Network que les appels partent vers le backend
3. Tester l'inscription/connexion

### 🔍 Debugging

#### Logs Backend :
- Disponibles dans le dashboard Render
- Endpoint `/api/logs` pour les logs de session

#### Logs Frontend :
- Console navigateur (F12)
- Vérifier les erreurs CORS ou de connexion

### 📊 Monitoring

- **Health Check** : `/api/health`
- **Admin Panel** : Utiliser `admin_script.py` avec `ADMIN_KEY`
- **Base de données** : Dashboard Supabase

### 🚨 Dépannage

#### Erreur CORS :
- Vérifier que `CORS(app, origins="*")` est configuré
- Vérifier l'URL du frontend dans les variables d'environnement

#### Erreur Base de données :
- Vérifier `DATABASE_URL` dans les variables d'environnement
- Tester la connexion Supabase

#### Build Frontend échoue :
- Vérifier `package.json` et `vite.config.js`
- S'assurer que `npm run build` fonctionne en local

### ✅ Checklist de Déploiement

- [ ] Repository GitHub configuré
- [ ] Services Render créés (backend + frontend)
- [ ] Variables d'environnement configurées
- [ ] Auto-deploy activé
- [ ] Test `/api/health` réussi
- [ ] Test frontend → backend réussi
- [ ] Test inscription/connexion réussi

### 🎯 URLs Finales

- **Backend** : https://yt-saas-backend.onrender.com
- **Frontend** : https://yt-saas-frontend.onrender.com
- **API Health** : https://yt-saas-backend.onrender.com/api/health
