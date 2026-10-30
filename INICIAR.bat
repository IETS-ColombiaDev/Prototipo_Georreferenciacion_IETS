@echo off
setlocal
cd /d "%~dp0"
title Observatorio IETS - Geoportal local
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import geopandas,pyogrio,pyarrow" >nul 2>&1
  if not errorlevel 1 (
    ".venv\Scripts\python.exe" servidor.py --open
    goto fin
  )
)
echo El entorno de lectura geografica no esta disponible.
echo Ejecute INSTALAR.bat una vez y vuelva a abrir INICIAR.bat.
echo Para consultar el ejemplo sin leer nuevas carpetas, abra ABRIR_SIN_SERVIDOR.html.
pause
:fin
endlocal
