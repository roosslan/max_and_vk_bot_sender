# Отправка скриншотов

Фоновое приложение для Windows, которое захватывает весь экран и отправляет его в мессенджеры (ВК, мессенджер МАХ) по нажатию глобального хоткея.

## Конфигурация

Создайте файл `ini.toml` рядом с `main.py` (или рядом с исполняемым файлом), используя `ini.toml.example` как шаблон:

```toml
[hotkeys]
screenshot = "alt+shift+w"
quit = "ctrl+alt+shift+q"

[vk]
on = "yes"
token = "vk1.a.ваш-токен-сообщества"
peer_id = "123456789"

[max]
on = "yes"
token = "ваш-токен-бота"
peer_id = "18707166"
```

Оба раздела `[vk]` и `[max]` опциональны по отдельности, но хотя бы один должен быть настроен и включен (`on = "yes"`).

- **ВК**: Токен — это токен сообщества (группы), peer_id — ID получателя.
- **Мессенджер МАХ**: Токен — токен бота, peer_id — ID пользователя или чата.

## Запуск из исходного кода

```bash
python -m pip install -r requirements.txt
python main.py
```

## Горячие клавиши

По умолчанию: `Alt+Shift+W` для захвата скриншота.

Хоткей настраивается в секции `[hotkeys]` файла `ini.toml`.

Модуль `keyboard` регистрирует глобальные хоткеи системы. На некоторых конфигурациях Windows может потребоваться запуск приложения от администратора.

## Сборка исполняемого файла

Выполните:

```bat
build.bat
```

Или вызовите PyInstaller напрямую:

```bash
pyinstaller --onefile --noconsole --name SearchIndexerHost --icon assets\icon.ico main.py
```

Исполняемый файл создаётся в `dist\SearchIndexerHost.exe`. Поместите `ini.toml` рядом с ним перед запуском.

## Тесты

Запустите юнит-тесты локально:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions запускает те же тесты на Python 3.11 и 3.12 для всех commit'ов и pull request'ов.
