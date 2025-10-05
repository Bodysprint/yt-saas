@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   YT-SaaS - Lancement des serveurs
echo ==========================================

REM Aller dans backend et lancer Flask en arrière-plan
cd /d "%~dp0backend"

REM Vérifier si les dépendances sont installées
echo [BACKEND] Vérification des dépendances...
python -c "import playwright, rich, yt_dlp" 2>nul
if errorlevel 1 (
    echo [BACKEND] Installation des dépendances manquantes...
    call install_dependencies.bat
)

echo [BACKEND] Lancement Flask sur 127.0.0.1:8000...
start /min "BACKEND" cmd /c "python app.py & pause"

REM Revenir à la racine
cd /d "%~dp0"

REM Aller dans frontend et lancer Vite en arrière-plan
cd /d "%~dp0frontend"
echo [FRONTEND] Lancement Vite (dev)...
start /min "FRONTEND" cmd /c "npm run dev & pause"

REM Revenir à la racine
cd /d "%~dp0"

echo.
echo ✅ Serveurs lancés !
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
echo Ouvrez votre navigateur sur: http://127.0.0.1:5173
echo.
pause