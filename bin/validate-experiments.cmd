@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%ROOT%validate_experiments.py" %*
) else (
  python "%ROOT%validate_experiments.py" %*
)
