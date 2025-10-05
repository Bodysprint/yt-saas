@echo off
echo ==========================================
echo   Installation des dependances Python
echo ==========================================

echo Installation des packages Python...
pip install -r requirements.txt

echo.
echo Installation des navigateurs Playwright...
playwright install

echo.
echo ==========================================
echo   Installation terminee !
echo ==========================================
pause
