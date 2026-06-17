@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%ROOT%search.py" %*
) else (
  python "%ROOT%search.py" %*
)
