@echo off
echo ========================================
echo   DIAGNOSTIC PYTHON - EXPERTS IA
echo ========================================
echo.

echo Test 1: Commande 'python'
python --version
echo Erreur level: %errorlevel%
echo.

echo Test 2: Commande 'py'  
py --version
echo Erreur level: %errorlevel%
echo.

echo Test 3: Commande 'python3'
python3 --version
echo Erreur level: %errorlevel%
echo.

echo Test 4: Verification PATH
echo PATH contient:
echo %PATH% | findstr /i python
echo.

echo Test 5: Recherche installation Python
dir "C:\Users\%USERNAME%\AppData\Local\Programs\Python" 2>nul
dir "C:\Python*" 2>nul
dir "C:\Program Files\Python*" 2>nul
echo.

echo Test 6: Verification alias Microsoft Store
echo Verification des alias...
where python
where py
echo.

pause