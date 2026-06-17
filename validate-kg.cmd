@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%ROOT%validate_kg.py" %*
) else (
  python "%ROOT%validate_kg.py" %*
)
