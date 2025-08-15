@echo off
echo ========================================
echo   TEST AUTHENTIFICATION - EXPERTS IA
echo ========================================
echo.
echo Ce script active temporairement l'authentification
echo pour tester la page de connexion en local.
echo.
echo Pour utiliser:
echo 1. Lancez ce script
echo 2. Mot de passe: test123
echo 3. Pour revenir en mode normal, fermez et relancez Run.bat
echo.
pause

REM Créer un fichier .env temporaire avec authentification
echo DEV_MODE=false > .env
echo APP_PASSWORD=test123 >> .env
echo LOG_LEVEL=DEBUG >> .env
echo ENABLE_SECURITY_LOGGING=true >> .env

echo Configuration temporaire créée...
echo Mot de passe de test: test123
echo.

REM Trouver Python
python --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

py --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found_python
)

python3 --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

echo ERREUR: Python non trouvé
pause
exit /b 1

:found_python
echo Démarrage EXPERTS IA avec authentification...
echo Interface: http://localhost:8501
echo Mot de passe: test123
echo.

%PYTHON_CMD% -m streamlit run app.py

REM Nettoyer le fichier .env temporaire
if exist .env del .env
echo.
echo Configuration temporaire supprimée.
pause