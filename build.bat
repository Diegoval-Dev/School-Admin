@echo off
setlocal
cd /d "%~dp0"

set /p VERSION=<version.txt

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m venv .venv-build || exit /b 1
call .venv-build\Scripts\activate.bat || exit /b 1
python -m pip install -r requirements-dev.txt || exit /b 1

python -m pytest -q || exit /b 1
python manage.py collectstatic --noinput || exit /b 1
python tools\make_icon.py || exit /b 1
pyinstaller colegio.spec --noconfirm || exit /b 1
iscc /DAppVersion=%VERSION% installer\colegio.iss || exit /b 1

echo Instalador listo en dist\Setup_ColegioJGC_v%VERSION%.exe
