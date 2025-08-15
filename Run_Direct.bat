@echo off
echo ========================================
echo   EXPERTS IA - LANCEMENT DIRECT
echo ========================================
echo.

REM Essayer les chemins Python les plus courants
set "PYTHON_PATHS=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
set "PYTHON_PATHS=%PYTHON_PATHS% C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
set "PYTHON_PATHS=%PYTHON_PATHS% C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
set "PYTHON_PATHS=%PYTHON_PATHS% C:\Python313\python.exe"
set "PYTHON_PATHS=%PYTHON_PATHS% C:\Python312\python.exe"
set "PYTHON_PATHS=%PYTHON_PATHS% C:\Program Files\Python313\python.exe"

echo Recherche Python dans les emplacements standards...

for %%P in (%PYTHON_PATHS%) do (
    if exist "%%P" (
        echo Python trouvé: %%P
        echo.
        echo Démarrage de EXPERTS IA...
        "%%P" -m streamlit run app.py --server.headless=false
        goto :end
    )
)

echo.
echo PYTHON NON TROUVE dans les emplacements standards.
echo.
echo Locations testées:
for %%P in (%PYTHON_PATHS%) do echo - %%P
echo.
echo SOLUTIONS:
echo 1. Lancez Debug_Python.bat pour diagnostic complet
echo 2. Réparez votre installation Python
echo 3. Redémarrez après avoir coché "Add to PATH"
echo.

:end
pause