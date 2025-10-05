from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import subprocess
import sys
from pathlib import Path
import hashlib
from logger import logger
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration de la base de données Supabase
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///users.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
TRIAL_LIMIT = int(os.getenv('TRIAL_LIMIT', '3'))
ADMIN_KEY = os.getenv('ADMIN_KEY', 'dev-admin-key')

app.config['SECRET_KEY'] = SECRET_KEY

# Configuration SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle User pour Supabase
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    premium = Column(Boolean, default=False)
    trial_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Configuration CORS pour les origines frontend
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5173", "http://localhost:5173"]}},
     supports_credentials=True)

# Chemins basés sur le répertoire du script
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
CHANNELS_FILE = BASE_DIR / "channels.txt"
URLS_FILE = BASE_DIR / "urls.txt"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"

# Créer le dossier transcripts s'il n'existe pas
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Variables globales pour suivre les processus en cours
SCRAPE_PROCESS = None
TRANSCRIBE_PROCESS = None

def load_users():
    """Charge les utilisateurs depuis le fichier JSON"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Sauvegarde les utilisateurs dans le fichier JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Hash simple du mot de passe (pour MVP)"""
    return hashlib.sha256(password.encode()).hexdigest()

# Fonctions utilitaires pour la gestion des utilisateurs avec SQLAlchemy
def get_db():
    """Obtient une session de base de données"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def get_user_by_email(email):
    """Récupère un utilisateur par email"""
    db = get_db()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()

def create_user(email, password_hash):
    """Crée un nouvel utilisateur"""
    db = get_db()
    try:
        import uuid
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=password_hash,
            premium=False,
            trial_count=0
        )
        db.add(user)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def increment_trial_count(email):
    """Incrémente le compteur d'essais d'un utilisateur"""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.trial_count += 1
            db.commit()
            return user.trial_count
        return None
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def can_user_transcribe(email):
    """Vérifie si un utilisateur peut transcrire (premium ou essais restants)"""
    user = get_user_by_email(email)
    if not user:
        return False, "Utilisateur non trouvé"
    
    if user.premium:
        return True, "Compte premium"
    
    if user.trial_count < TRIAL_LIMIT:
        return True, f"Essais restants: {TRIAL_LIMIT - user.trial_count}"
    
    return False, f"Limite d'essais atteinte ({TRIAL_LIMIT})"

# Décorateur pour l'authentification admin
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-Admin-Key")
        if key != ADMIN_KEY:
            return jsonify({"error": "forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/api/health", methods=["GET"])
def health():
    """Healthcheck endpoint"""
    logger.log_info("Healthcheck appelé")
    return jsonify({"status": "ok"})

@app.route("/api/test-transcription", methods=["POST"])
def test_transcription():
    """Test de transcription pour diagnostiquer les problèmes"""
    try:
        # Créer un fichier urls.txt de test avec une URL simple
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll pour test
        with open(URLS_FILE, 'w', encoding='utf-8') as f:
            f.write(test_url)
        
        print(f"Test de transcription avec: {test_url}")
        
        # Lancer le script de transcription
        script_path = BASE_DIR / "lancer_bot (2).bat"
        result = subprocess.run(
            ["cmd", "/c", str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return jsonify({
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "script_path": str(script_path),
            "urls_file_exists": URLS_FILE.exists(),
            "urls_content": URLS_FILE.read_text(encoding='utf-8') if URLS_FILE.exists() else "Fichier non trouvé"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors du test: {str(e)}"}), 500

@app.route("/api/debug", methods=["GET"])
def debug():
    """Debug endpoint pour vérifier les fichiers"""
    files_status = {
        "scrape_script": (BASE_DIR / "scrape_channel_videos.py").exists(),
        "transcribe_script": (BASE_DIR / "lancer_bot (2).bat").exists(),
        "bot_script": (BASE_DIR / "bot_yttotranscript.py").exists(),
        "channels_file": CHANNELS_FILE.exists(),
        "urls_file": URLS_FILE.exists(),
        "transcripts_dir": TRANSCRIPTS_DIR.exists(),
        "transcripts_count": len(list(TRANSCRIPTS_DIR.glob("*.txt"))) if TRANSCRIPTS_DIR.exists() else 0,
        "dependencies": {
            "playwright": False,
            "rich": False,
            "yt_dlp": False,
            "requests": False
        }
    }
    
    # Vérifier les dépendances Python
    try:
        import playwright
        files_status["dependencies"]["playwright"] = True
    except ImportError:
        pass
    
    try:
        import rich
        files_status["dependencies"]["rich"] = True
    except ImportError:
        pass
    
    try:
        import yt_dlp
        files_status["dependencies"]["yt_dlp"] = True
    except ImportError:
        pass
    
    try:
        import requests
        files_status["dependencies"]["requests"] = True
    except ImportError:
        pass
    
    return jsonify(files_status)

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Inscription d'un nouvel utilisateur avec SQLAlchemy"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = get_user_by_email(email)
    if existing_user:
        return jsonify({"error": "Utilisateur déjà existant"}), 400
    
    try:
        # Créer le nouvel utilisateur
        user = create_user(email, hash_password(password))
        logger.log_success(f"Nouvel utilisateur créé: {email}")
        
        return jsonify({
            "message": "Inscription réussie",
            "user": {
                "email": user.email,
                "premium": user.premium,
                "trial_count": user.trial_count
            }
        }), 201
    except Exception as e:
        logger.log_error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
        return jsonify({"error": "Erreur lors de l'inscription"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Connexion d'un utilisateur avec SQLAlchemy"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400
    
    # Récupérer l'utilisateur depuis la base de données
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    if user.password_hash != hash_password(password):
        return jsonify({"error": "Mot de passe incorrect"}), 401
    
    logger.log_success(f"Connexion réussie: {email}")
    
    return jsonify({
        "message": "Connexion réussie",
        "token": "dev-token",  # Token simple pour le MVP
        "user": {
            "email": user.email,
            "premium": user.premium,
            "trial_count": user.trial_count,
            "trial_limit": TRIAL_LIMIT
        }
    }), 200

@app.route("/api/scrape/channel", methods=["POST"])
def scrape_channel():
    """Scrape une chaîne YouTube en utilisant le script existant"""
    global SCRAPE_PROCESS
    data = request.get_json()
    channel = data.get("channel")
    
    logger.log_api_call("/api/scrape/channel", "POST", data)
    
    if not channel:
        logger.log_error("Channel requis manquant")
        return jsonify({"error": "Channel requis"}), 400
    
    try:
        # Nettoyer les anciens fichiers avant de commencer
        if URLS_FILE.exists():
            URLS_FILE.unlink()
            logger.log_file_operation("SUPPRESSION", str(URLS_FILE), "Nettoyage avant nouveau scraping")
        
        # Écrire la chaîne dans channels.txt
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            f.write(channel)
        
        logger.log_file_operation("ÉCRITURE", str(CHANNELS_FILE), f"Contenu: {channel}")
        
        # Lancer le script de scraping en arrière-plan
        script_path = BASE_DIR / "scrape_channel_videos.py"
        logger.log_scraping(channel, 0, "DÉBUT")
        print(f"Lancement du scraping pour: {channel}")
        
        # Lancer en arrière-plan avec Popen
        SCRAPE_PROCESS = subprocess.Popen(
            ["python", str(script_path)],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.log_scraping(channel, 0, "LANCÉ")
        print(f"Processus de scraping lancé avec PID: {SCRAPE_PROCESS.pid}")
        
        return jsonify({
            "message": "Scraping démarré",
            "status": "started",
            "process_id": SCRAPE_PROCESS.pid
        }), 202
        
    except Exception as e:
        print(f"Exception lors du scraping: {str(e)}")
        return jsonify({"error": f"Erreur lors du scraping: {str(e)}"}), 500

@app.route("/api/transcribe/selected", methods=["POST"])
def transcribe_selected():
    """Transcrire seulement les vidéos sélectionnées"""
    global TRANSCRIBE_PROCESS
    data = request.get_json()
    urls = data.get("urls", [])
    user_email = data.get("email")  # Email de l'utilisateur connecté
    
    logger.log_api_call("/api/transcribe/selected", "POST", data)
    
    if not urls:
        logger.log_error("Aucune URL fournie pour la transcription")
        return jsonify({"error": "Aucune URL fournie"}), 400
    
    # Vérifier les limites d'utilisation si un email est fourni
    if user_email:
        can_transcribe, message = check_transcription_limit(user_email)
        if not can_transcribe:
            logger.log_warning(f"Tentative de transcription bloquée pour {user_email}: {message}")
            return jsonify({
                "error": f"Limite d'utilisation atteinte: {message}",
                "trial_limit_reached": True
            }), 403
    
    try:
        # Écrire les URLs sélectionnées dans urls.txt
        with open(URLS_FILE, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(urls))
        
        logger.log_file_operation("ÉCRITURE", str(URLS_FILE), f"URLs sélectionnées: {len(urls)}")
        print(f"Transcription de {len(urls)} vidéos sélectionnées")
        
        # Lancer le script de transcription ORIGINAL avec Playwright
        script_path = BASE_DIR / "bot_yttotranscript.py"
        
        logger.log_transcription("", "DÉBUT", f"Script: {script_path}")
        print(f"Lancement de la transcription pour {len(urls)} vidéos...")
        print(f"Script utilisé: {script_path}")
        print(f"URLs à transcrire: {urls}")
        
        # Vérifier que urls.txt contient bien les URLs
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Contenu de urls.txt: {content[:200]}...")
        
        try:
            # Lancer directement le script avec cmd pour garantir l'affichage
            cmd_command = f'cmd /c "cd /d {BASE_DIR} && python bot_yttotranscript.py"'
            print(f"Commande exécutée: {cmd_command}")
            TRANSCRIBE_PROCESS = subprocess.Popen(
                cmd_command,
                shell=True,
                stdout=None,  # Pas de capture pour permettre l'affichage
                stderr=None,  # Pas de capture pour permettre l'affichage
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
            
            logger.log_transcription("", "LANCÉ", f"PID: {TRANSCRIBE_PROCESS.pid}")
            print(f"Processus de transcription lancé avec PID: {TRANSCRIBE_PROCESS.pid}")
            print("Le script de transcription va traiter les vidéos...")
            
            # Retourner immédiatement - la transcription continue en arrière-plan
            return jsonify({
                "message": f"Transcription démarrée ! Le script va traiter {len(urls)} vidéo(s)",
                "process_id": TRANSCRIBE_PROCESS.pid,
                "status": "started",
                "note": "Vérifiez les logs pour suivre la progression"
            }), 202
                
        except Exception as e:
            print(f"Erreur lors du lancement: {e}")
            return jsonify({
                "error": f"Erreur lors du lancement de la transcription: {str(e)}"
            }), 500
        
    except Exception as e:
        print(f"Exception lors de la transcription: {str(e)}")
        return jsonify({"error": f"Erreur lors de la transcription: {str(e)}"}), 500

@app.route("/api/transcribe/bulk", methods=["POST"])
def transcribe_bulk():
    """Lance la transcription en bulk avec le script existant"""
    global TRANSCRIBE_PROCESS
    data = request.get_json() or {}
    user_email = data.get("email")  # Email de l'utilisateur connecté
    
    # Vérifier les limites d'utilisation si un email est fourni
    if user_email:
        can_transcribe, message = check_transcription_limit(user_email)
        if not can_transcribe:
            logger.log_warning(f"Tentative de transcription bulk bloquée pour {user_email}: {message}")
            return jsonify({
                "error": f"Limite d'utilisation atteinte: {message}",
                "trial_limit_reached": True
            }), 403
    
    try:
        # Lancer le script de transcription existant
        script_path = BASE_DIR / "lancer_bot (2).bat"
        print(f"Lancement de la transcription: {script_path}")
        
        # Vérifier que le fichier .bat existe
        if not script_path.exists():
            print(f"Fichier .bat non trouvé: {script_path}")
            # Fallback: utiliser directement le script Python
            script_path = BASE_DIR / "bot_yttotranscript.py"
            if not script_path.exists():
                return jsonify({"error": "Script de transcription non trouvé"}), 500
            print(f"Utilisation du script Python: {script_path}")
        
        # Lancer en arrière-plan avec Popen (asynchrone)
        try:
            # Essayer d'abord avec le .bat
            if str(script_path).endswith('.bat'):
                TRANSCRIBE_PROCESS = subprocess.Popen(
                    ["cmd", "/c", str(script_path)],
                    cwd=str(BASE_DIR),
                    stdout=None,  # Pas de capture pour permettre l'affichage
                    stderr=None,  # Pas de capture pour permettre l'affichage
                    text=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
                )
            else:
                # Fallback: script Python direct
                TRANSCRIBE_PROCESS = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(BASE_DIR),
                    stdout=None,  # Pas de capture pour permettre l'affichage
                    stderr=None,  # Pas de capture pour permettre l'affichage
                    text=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
                )
            
            print(f"Processus de transcription lancé avec PID: {TRANSCRIBE_PROCESS.pid}")
            logger.log_transcription("", "LANCÉ", f"PID: {TRANSCRIBE_PROCESS.pid}")
            
            # Retourner immédiatement - la transcription continue en arrière-plan
            return jsonify({
                "message": "Transcription démarrée ! Le script va traiter les vidéos en arrière-plan",
                "process_id": TRANSCRIBE_PROCESS.pid,
                "status": "started",
                "note": "Vérifiez les logs pour suivre la progression"
            }), 202
                
        except FileNotFoundError as e:
            print(f"Erreur fichier non trouvé: {e}")
            return jsonify({"error": f"Script de transcription non trouvé: {e}"}), 500
        except Exception as e:
            print(f"Erreur lors du lancement: {e}")
            return jsonify({"error": f"Erreur lors du lancement de la transcription: {str(e)}"}), 500
        
    except Exception as e:
        print(f"Exception lors de la transcription: {str(e)}")
        return jsonify({"error": f"Erreur lors de la transcription: {str(e)}"}), 500

def get_video_info_from_url(url):
    """Extrait l'ID vidéo depuis l'URL YouTube"""
    import re
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id_match.group(1) if video_id_match else None

def get_video_title(video_id):
    """Récupère le titre d'une vidéo YouTube via l'API publique"""
    try:
        import requests
        import re
        
        # Utiliser l'API publique de YouTube (sans clé API)
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            # Extraire le titre depuis la page HTML
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                title = title_match.group(1)
                # Nettoyer le titre (enlever " - YouTube")
                title = title.replace(' - YouTube', '').strip()
                return title
    except Exception as e:
        print(f"Erreur lors de la récupération du titre pour {video_id}: {e}")
    
    return None

@app.route("/api/scraped-urls", methods=["GET"])
def get_scraped_urls():
    """Récupère les URLs scrapées depuis urls.txt avec infos vidéo"""
    try:
        urls = []
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
        
        # Enrichir avec les infos vidéo
        videos_with_info = []
        for i, url in enumerate(urls):
            video_id = get_video_info_from_url(url)
            title = get_video_title(video_id) if video_id else f"Vidéo {i + 1}"
            videos_with_info.append({
                "url": url,
                "video_id": video_id,
                "title": title,
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else None
            })
        
        return jsonify({"videos": videos_with_info, "count": len(videos_with_info)}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture des URLs: {str(e)}"}), 500

@app.route("/api/transcripts", methods=["GET"])
def list_transcripts():
    """Liste tous les fichiers de transcription disponibles"""
    try:
        files = []
        if TRANSCRIPTS_DIR.exists():
            for file_path in TRANSCRIPTS_DIR.glob("*.txt"):
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(BASE_DIR)),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        return jsonify({"files": files}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture des fichiers: {str(e)}"}), 500

@app.route("/api/transcripts/content", methods=["GET"])
def get_transcript_content():
    """Récupère le contenu d'un fichier de transcription"""
    path = request.args.get("path")
    
    if not path:
        return jsonify({"error": "Paramètre path requis"}), 400
    
    try:
        # Sécuriser le chemin pour éviter les accès en dehors du dossier transcripts
        safe_path = Path(path)
        if ".." in str(safe_path) or not str(safe_path).startswith("transcripts"):
            return jsonify({"error": "Chemin non autorisé"}), 400
        
        file_path = BASE_DIR / safe_path
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({"error": "Fichier non trouvé"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({"content": content}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture du fichier: {str(e)}"}), 500

@app.route("/api/transcripts/download", methods=["GET"])
def download_all_transcripts():
    """Télécharge tous les fichiers de transcription dans un ZIP"""
    try:
        import zipfile
        import tempfile
        
        # Créer un fichier ZIP temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            zip_path = temp_zip.name
        
        # Créer le ZIP avec tous les fichiers de transcription
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            if TRANSCRIPTS_DIR.exists():
                for file_path in TRANSCRIPTS_DIR.glob("*.txt"):
                    zipf.write(file_path, file_path.name)
        
        # Retourner le fichier ZIP
        return send_from_directory(
            os.path.dirname(zip_path),
            os.path.basename(zip_path),
            as_attachment=True,
            download_name="transcriptions.zip"
        )
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la création du ZIP: {str(e)}"}), 500

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Récupère les logs de la session actuelle"""
    try:
        log_file = BASE_DIR / "session_log.txt"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
            return jsonify({"logs": logs}), 200
        else:
            return jsonify({"logs": "Aucun log disponible"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture des logs: {str(e)}"}), 500

@app.route("/api/scrape/status", methods=["GET"])
def get_scrape_status():
    """Vérifie le statut du scraping en cours"""
    global SCRAPE_PROCESS
    try:
        running = False
        if SCRAPE_PROCESS is not None:
            # Vérifier si le processus est encore en cours
            poll_result = SCRAPE_PROCESS.poll()
            if poll_result is None:
                running = True
            else:
                # Processus terminé, nettoyer
                print(f"DEBUG: Processus scraping terminé avec code: {poll_result}")
                SCRAPE_PROCESS = None
        
        # Vérifier le signal de fin d'enrichissement
        completion_file = BASE_DIR / "scraping_completed.txt"
        if completion_file.exists():
            try:
                with open(completion_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content.startswith("completed:"):
                    # Enrichissement terminé, nettoyer le signal
                    completion_file.unlink()
                    print("DEBUG: Signal de fin d'enrichissement détecté, processus terminé")
                    running = False
                    if SCRAPE_PROCESS is not None:
                        try:
                            SCRAPE_PROCESS.terminate()
                            print("DEBUG: Processus de scraping terminé")
                        except:
                            pass
                        SCRAPE_PROCESS = None
            except Exception as e:
                print(f"DEBUG: Erreur lecture signal de fin: {e}")
        
        # Compter les URLs dans urls.txt
        url_count = 0
        last_modified = None
        if URLS_FILE.exists():
            try:
                with open(URLS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Essayer de lire comme JSON
                    try:
                        videos_data = json.loads(content)
                        if isinstance(videos_data, list):
                            url_count = len(videos_data)
                        else:
                            # Ancien format
                            urls = [line.strip() for line in content.splitlines() if line.strip()]
                            url_count = len(urls)
                    except (json.JSONDecodeError, ValueError):
                        # Ancien format
                        urls = [line.strip() for line in content.splitlines() if line.strip()]
                        url_count = len(urls)
                last_modified = URLS_FILE.stat().st_mtime
                print(f"DEBUG: {url_count} vidéos trouvées dans urls.txt")
            except Exception as e:
                print(f"DEBUG: Erreur lecture urls.txt: {e}")
                url_count = 0
        
        return jsonify({
            "running": running,
            "count": url_count,
            "lastModified": last_modified
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la vérification du statut: {str(e)}"}), 500

@app.route("/api/scrape/urls", methods=["GET"])
def get_scrape_urls():
    """Récupère les URLs scrapées en temps réel avec titres réels"""
    try:
        videos_with_info = []
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Essayer de lire comme JSON d'abord (nouveau format)
            try:
                videos_data = json.loads(content)
                if isinstance(videos_data, list):
                    # Nouveau format JSON avec titres réels
                    videos_with_info = []
                    for video in videos_data:
                        videos_with_info.append({
                            "url": video.get("url", ""),
                            "video_id": video.get("video_id", ""),
                            "title": video.get("title", "Titre non disponible"),
                            "thumbnail": video.get("thumbnail", f"https://img.youtube.com/vi/{video.get('video_id', '')}/mqdefault.jpg" if video.get('video_id') else None)
                        })
                    print(f"DEBUG: Lecture JSON de {len(videos_with_info)} vidéos avec titres réels")
                else:
                    raise ValueError("Format JSON invalide")
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fallback: ancien format (une URL par ligne)
                print("DEBUG: Format ancien détecté, conversion en cours...")
                urls = [line.strip() for line in content.splitlines() if line.strip()]
                for i, url in enumerate(urls):
                    video_id = get_video_info_from_url(url)
                    videos_with_info.append({
                        "url": url,
                        "video_id": video_id,
                        "title": f"Vidéo {i + 1}",
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else None
                    })
                print(f"DEBUG: Conversion de {len(videos_with_info)} URLs (format ancien)")
        else:
            print("DEBUG: urls.txt n'existe pas")
        
        print(f"DEBUG: Retour de {len(videos_with_info)} vidéos")
        
        return jsonify({
            "urls": videos_with_info,
            "count": len(videos_with_info),
            "lastModified": URLS_FILE.stat().st_mtime if URLS_FILE.exists() else None
        }), 200
    except Exception as e:
        print(f"DEBUG: Erreur dans get_scrape_urls: {e}")
        return jsonify({"error": f"Erreur lors de la lecture des URLs: {str(e)}"}), 500

@app.route("/api/transcribe/status", methods=["GET"])
def get_transcribe_status():
    """Vérifie le statut de la transcription en cours"""
    global TRANSCRIBE_PROCESS
    try:
        running = False
        if TRANSCRIBE_PROCESS is not None:
            # Vérifier si le processus est encore en cours
            poll_result = TRANSCRIBE_PROCESS.poll()
            if poll_result is None:
                running = True
            else:
                # Processus terminé, nettoyer
                print(f"DEBUG: Processus transcription terminé avec code: {poll_result}")
                TRANSCRIBE_PROCESS = None
        
        # Compter les fichiers de transcription
        files_count = 0
        files = []
        if TRANSCRIPTS_DIR.exists():
            transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
            files_count = len(transcript_files)
            files = [f.name for f in transcript_files]
            print(f"DEBUG: {files_count} fichiers de transcription trouvés: {files}")
        else:
            print("DEBUG: Dossier transcripts n'existe pas")
        
        return jsonify({
            "running": running,
            "filesCount": files_count,
            "files": files
        }), 200
    except Exception as e:
        print(f"DEBUG: Erreur dans get_transcribe_status: {e}")
        return jsonify({"error": f"Erreur lors de la vérification du statut: {str(e)}"}), 500

@app.route("/api/transcription/status", methods=["GET"])
def get_transcription_status():
    """Vérifie le statut de la transcription en cours (legacy)"""
    try:
        completion_file = BASE_DIR / "transcription_completed.txt"
        if completion_file.exists():
            with open(completion_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content.startswith("completed:"):
                parts = content.split(":")
                success_count = int(parts[1]) if len(parts) > 1 else 0
                total_count = int(parts[2]) if len(parts) > 2 else 0
                
                # Supprimer le fichier de signal
                completion_file.unlink()
                
                return jsonify({
                    "status": "completed",
                    "success_count": success_count,
                    "total_count": total_count
                }), 200
            else:
                return jsonify({"status": "unknown"}), 200
        else:
            return jsonify({"status": "running"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la vérification du statut: {str(e)}"}), 500

@app.route("/api/transcripts/clean", methods=["POST"])
def clean_old_transcripts():
    """Nettoie les anciens fichiers de transcription"""
    try:
        if TRANSCRIPTS_DIR.exists():
            # Supprimer tous les fichiers .txt dans le dossier transcripts
            for file_path in TRANSCRIPTS_DIR.glob("*.txt"):
                file_path.unlink()
                logger.log_file_operation("SUPPRESSION", str(file_path), "Nettoyage anciens transcripts")
        
        return jsonify({"message": "Anciens fichiers de transcription supprimés"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors du nettoyage: {str(e)}"}), 500

@app.route("/api/scrape/urls/enriched", methods=["GET"])
def get_scrape_urls_enriched():
    """Récupère les URLs avec titres enrichis (maintenant identique à /urls)"""
    try:
        # Maintenant que les titres sont directement dans le JSON, 
        # cet endpoint retourne la même chose que /urls
        videos_with_info = []
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Essayer de lire comme JSON d'abord (nouveau format)
            try:
                videos_data = json.loads(content)
                if isinstance(videos_data, list):
                    # Nouveau format JSON avec titres réels
                    videos_with_info = []
                    for video in videos_data:
                        videos_with_info.append({
                            "url": video.get("url", ""),
                            "video_id": video.get("video_id", ""),
                            "title": video.get("title", "Titre non disponible"),
                            "thumbnail": video.get("thumbnail", f"https://img.youtube.com/vi/{video.get('video_id', '')}/mqdefault.jpg" if video.get('video_id') else None)
                        })
                    print(f"DEBUG: Lecture JSON ENRICHI de {len(videos_with_info)} vidéos avec titres réels")
                else:
                    raise ValueError("Format JSON invalide")
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fallback: ancien format (une URL par ligne) - enrichir avec API
                print("DEBUG: Format ancien détecté, enrichissement avec API...")
                urls = [line.strip() for line in content.splitlines() if line.strip()]
                for i, url in enumerate(urls):
                    video_id = get_video_info_from_url(url)
                    title = get_video_title(video_id) if video_id else f"Vidéo {i + 1}"
                    videos_with_info.append({
                        "url": url,
                        "video_id": video_id,
                        "title": title,
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else None
                    })
                print(f"DEBUG: Enrichissement API de {len(videos_with_info)} URLs (format ancien)")
        else:
            print("DEBUG: urls.txt n'existe pas")
        
        print(f"DEBUG: Retour ENRICHI de {len(videos_with_info)} vidéos")
        
        return jsonify({
            "urls": videos_with_info,
            "count": len(videos_with_info),
            "lastModified": URLS_FILE.stat().st_mtime if URLS_FILE.exists() else None
        }), 200
    except Exception as e:
        print(f"DEBUG: Erreur dans get_scrape_urls_enriched: {e}")
        return jsonify({"error": f"Erreur lors de la lecture des URLs: {str(e)}"}), 500

@app.route("/api/debug/urls", methods=["GET"])
def debug_urls():
    """Debug endpoint pour vérifier le contenu de urls.txt"""
    try:
        if URLS_FILE.exists():
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line.strip() for line in content.splitlines() if line.strip()]
            
            return jsonify({
                "exists": True,
                "content": content,
                "lines": lines,
                "count": len(lines),
                "size": len(content),
                "lastModified": URLS_FILE.stat().st_mtime
            }), 200
        else:
            return jsonify({
                "exists": False,
                "message": "urls.txt n'existe pas"
            }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route("/api/debug/transcripts", methods=["GET"])
def debug_transcripts():
    """Debug endpoint pour vérifier les fichiers de transcription"""
    try:
        transcript_files = []
        if TRANSCRIPTS_DIR.exists():
            for file_path in TRANSCRIPTS_DIR.glob("*.txt"):
                stat = file_path.stat()
                transcript_files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        return jsonify({
            "transcripts_dir_exists": TRANSCRIPTS_DIR.exists(),
            "transcripts_dir_path": str(TRANSCRIPTS_DIR),
            "files": transcript_files,
            "count": len(transcript_files)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

# ===== ROUTES D'ADMINISTRATION =====

@app.route("/api/admin/set-premium", methods=["POST"])
@admin_required
def set_premium():
    """Active/désactive le statut premium d'un utilisateur"""
    data = request.get_json()
    email = data.get("email")
    premium = bool(data.get("premium", False))
    
    if not email:
        return jsonify({"error": "Email requis"}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    # Mettre à jour le statut premium
    db = get_db()
    try:
        user.premium = premium
        db.commit()
        logger.log_success(f"Statut premium mis à jour pour {email}: {premium}")
        
        return jsonify({
            "message": "Statut premium mis à jour",
            "email": email,
            "premium": premium
        }), 200
    except Exception as e:
        db.rollback()
        logger.log_error(f"Erreur mise à jour premium: {str(e)}")
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500
    finally:
        db.close()

@app.route("/api/admin/users", methods=["GET"])
@admin_required
def list_users():
    """Liste tous les utilisateurs (admin seulement)"""
    db = get_db()
    try:
        users = db.query(User).all()
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "email": user.email,
                "premium": user.premium,
                "trial_count": user.trial_count,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            "users": users_data,
            "total": len(users_data)
        }), 200
    except Exception as e:
        logger.log_error(f"Erreur liste utilisateurs: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération des utilisateurs"}), 500
    finally:
        db.close()

@app.route("/api/admin/reset-trial", methods=["POST"])
@admin_required
def reset_trial():
    """Remet à zéro le compteur d'essais d'un utilisateur"""
    data = request.get_json()
    email = data.get("email")
    
    if not email:
        return jsonify({"error": "Email requis"}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    db = get_db()
    try:
        user.trial_count = 0
        db.commit()
        logger.log_success(f"Compteur d'essais remis à zéro pour {email}")
        
        return jsonify({
            "message": "Compteur d'essais remis à zéro",
            "email": email,
            "trial_count": 0
        }), 200
    except Exception as e:
        db.rollback()
        logger.log_error(f"Erreur reset trial: {str(e)}")
        return jsonify({"error": "Erreur lors de la remise à zéro"}), 500
    finally:
        db.close()

# ===== MODIFICATION DES ENDPOINTS DE TRANSCRIPTION =====

# Modifier l'endpoint de transcription pour vérifier les limites
def check_transcription_limit(email):
    """Vérifie si l'utilisateur peut transcrire et incrémente le compteur si nécessaire"""
    can_transcribe, message = can_user_transcribe(email)
    
    if not can_transcribe:
        return False, message
    
    # Incrémenter le compteur d'essais si l'utilisateur n'est pas premium
    user = get_user_by_email(email)
    if user and not user.premium:
        increment_trial_count(email)
        logger.log_info(f"Compteur d'essais incrémenté pour {email}")
    
    return True, message

if __name__ == "__main__":
    # Configuration pour Render (production)
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host="0.0.0.0", port=port, debug=debug)