@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "SCRIPT=%ROOT%validate_kg.py"

where python >nul 2>nul
if errorlevel 1 goto try_py
call python -c "import sys" >nul 2>nul
if errorlevel 1 goto try_py
call python "%SCRIPT%" %*
exit /b

:try_py
where py >nul 2>nul
if errorlevel 1 goto no_python
call py -3 "%SCRIPT%" %*
exit /b

:no_python
echo error: no usable Python interpreter found. Install Python 3 or fix the Windows py launcher configuration. 1>&2
exit /b 1
