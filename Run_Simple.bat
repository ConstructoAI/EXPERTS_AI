@echo off
echo ========================================
echo   EXPERTS IA - LANCEMENT SIMPLE
echo ========================================
echo.

echo Lancement avec ouverture automatique du navigateur...

REM Détection Python - Version améliorée
echo Recherche de Python...

REM Test 1: py (fonctionne selon diagnostic)
py --version 2>nul  
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :python_found
)

REM Test 2: python
python --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

REM Test 3: python3
python3 --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

REM Aucun Python trouvé
echo.
echo ========================================
echo PYTHON NON TROUVE - SOLUTIONS:
echo ========================================
echo.
echo 1. Verifiez que Python est installé:
echo    - Allez sur https://python.org
echo    - Téléchargez Python 3.9+ 
echo    - IMPORTANT: Cochez "Add Python to PATH"
echo.
echo 2. Si Python est installé, problème d'alias:
echo    - Paramètres Windows ^> Applications
echo    - Aliases d'exécution d'applications
echo    - Désactivez python.exe et python3.exe
echo.
echo 3. Redémarrez votre ordinateur après installation
echo.
echo 4. Lancez Debug_Python.bat pour plus d'infos
echo.
pause
exit /b 1

:python_found

echo Python trouvé: %PYTHON_CMD%
echo.

REM Démarrer Streamlit avec ouverture automatique
echo Démarrage en cours...
echo L'application va s'ouvrir dans votre navigateur dans 5 secondes...
echo.

%PYTHON_CMD% -m streamlit run app.py --server.headless=false --server.runOnSave=true

pause