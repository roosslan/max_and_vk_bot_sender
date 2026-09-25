@echo off
REM Собирает main.py в один exe-файл без консольного окна.
REM Требуется: pip install -r requirements.txt

pyinstaller --onefile --noconsole --name SearchIndexerHost --icon assets\icon.ico main.py

echo.
echo Готово. Файл: dist\SearchIndexerHost.exe
echo Не забудьте положить ini.toml рядом с exe перед запуском.
