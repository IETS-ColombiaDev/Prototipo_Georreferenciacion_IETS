@echo off
setlocal
cd /d "%~dp0"
title Preparar entorno local de IETS
echo Instala dependencias en .venv dentro de esta carpeta. Requiere internet.
py -3 -c "import sys; assert sys.version_info >= (3,12)" >nul 2>&1
if not errorlevel 1 (
  py -3 -m venv .venv
) else (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m venv .venv
  ) else (
    echo Se necesita Python 3.12 o superior. Instale Python y repita este paso.
    goto fin
  )
)
if errorlevel 1 goto fin
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fin
echo Entorno listo. Abra INICIAR.bat.
:fin
pause
endlocal
