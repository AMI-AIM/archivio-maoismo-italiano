@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: AMI - Deploy one-click (Windows)
:: ============================================================
:: Esegue in sequenza:
::   1. scripts\persone.py
::   2. scripts\org.py
::   3. scripts\generatore.py
::   4. git add, commit, push
:: ============================================================

:: Vai nella cartella del batch
cd /d "%~dp0"

:: Se il percorso contiene spazi, funziona uguale
set "ROOT_DIR=%cd%"

echo.
echo ============================================================
echo    AMI - Deploy one-click
echo ============================================================
echo    Data: %date% %time%
echo    Cartella: %ROOT_DIR%
echo ============================================================
echo.

:: Verifica che i file esistano
if not exist "scripts\persone.py" (
    echo [ERRORE] Non trovo scripts\persone.py
    echo.
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] scripts\persone.py trovato.

if not exist "scripts\org.py" (
    echo [ERRORE] Non trovo scripts\org.py
    echo.
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] scripts\org.py trovato.

if not exist "scripts\generatore.py" (
    echo [ERRORE] Non trovo scripts\generatore.py
    echo.
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] scripts\generatore.py trovato.
echo.

:: ============================================================
:: STEP 1: persone.py
:: ============================================================
echo [1/4] Esecuzione di scripts\persone.py...
python scripts\persone.py
if errorlevel 1 (
    echo.
    echo [ERRORE] persone.py fallito!
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] persone.py completato.
echo.

:: ============================================================
:: STEP 2: org.py
:: ============================================================
echo [2/4] Esecuzione di scripts\org.py...
python scripts\org.py
if errorlevel 1 (
    echo.
    echo [ERRORE] org.py fallito!
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] org.py completato.
echo.

:: ============================================================
:: STEP 3: generatore.py
:: ============================================================
echo [3/4] Esecuzione di scripts\generatore.py...
python scripts\generatore.py
if errorlevel 1 (
    echo.
    echo [ERRORE] generatore.py fallito!
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] generatore.py completato.
echo.

:: ============================================================
:: STEP 4: Push su GitHub
:: ============================================================
echo [4/4] Pubblicazione su GitHub...
echo.

:: Aggiungi tutti i file
echo   git add...
git add .
if errorlevel 1 (
    echo [AVVISO] git add fallito. Verifica di essere in un repository Git.
)

:: Commit automatico
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set "DATA=%%a-%%b-%%c"
for /f "tokens=1-2 delims=: " %%a in ("%time%") do set "ORA=%%a-%%b"
set "COMMIT_MSG=Aggiornamento sito AMI - %DATA% %ORA%"
echo   commit: "%COMMIT_MSG%"
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo [AVVISO] git commit fallito (potrebbe non esserci nulla da committare).
)

:: Push
echo   git push...
git push
if errorlevel 1 (
    echo.
    echo [ERRORE] git push fallito!
    echo Premi un tasto per uscire...
    pause >nul
    exit /b 1
)
echo [OK] Push completato.
echo.

:: ============================================================
:: RIEPILOGO
:: ============================================================
echo.
echo ============================================================
echo    DEPLOY COMPLETATO CON SUCCESSO!
echo ============================================================
echo.
pause