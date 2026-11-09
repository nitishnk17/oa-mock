@echo off
rem Start OA Mock (Windows): double-click this file. Stop it with Ctrl+C.
rem First time? Double-click scripts\setup.bat instead: it installs what's missing and adds the oa-mock command.
cd /d "%~dp0"
rem Copies from before the app moved into app\ (Nov 2026): fetch the new folders, drop the old empty one.
if not exist app\run.py (
  git config --get core.sparseCheckout 2>nul | findstr /x true >nul && (echo Fetching the app's new folders, one time... & git sparse-checkout add app scripts)
)
if exist oa_mock\__pycache__ if not exist oa_mock\*.py rd /s /q oa_mock
where py >nul 2>nul && (py -3 app\run.py %* & goto :eof)
python app\run.py %*
