@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
:: ========================================
:: Настройки окружения
:: ========================================
set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%venv"
set "REQUIREMENTS=%PROJECT_ROOT%requirements.txt"
set "DOT_ENV=%PROJECT_ROOT%.env"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"
set "XTUNNEL_URL=https://files.xtunnel.ru/xtunnel/1.0.14/xTunnel.win-x64.1.0.14.zip"
set "XTUNNEL_DIR=%PROJECT_ROOT%xtunnel"
set "XTUNNEL_EXE=%XTUNNEL_DIR%\xTunnel.exe"
:: ========================================
:: Главное меню
:: ========================================
:main
cls
echo.
echo ╔═══════════════════════════════════════════╗
echo ║  🚀 Кванториум Бот - Система управления   ║
echo ╚═══════════════════════════════════════════╝
echo.
echo 1. 🛠️  Установить зависимости и запустить
echo 2. ⚡ Только запустить
echo 3. 🚪 Выход
echo.
set /p choice="👉 Выберите действие: "
if "%choice%"=="1" goto full_install
if "%choice%"=="2" goto run_only
if "%choice%"=="3" exit /b
goto main

:: ========================================
:: Полная установка
:: ========================================
:full_install
call :check_python
call :create_dotenv
call :create_venv
call :install_dependencies
call :setup_xtunnel
goto run_components

:: ========================================
:: Только запуск
:: ========================================
:run_only
call :check_python
call :activate_venv
call :setup_xtunnel
goto run_components

:: ========================================
:: Проверка Python
:: ========================================
:check_python
echo.
echo 🔍 [1/5] Проверка Python...
python -c "import sys; exit(0) if sys.version_info >= (3, 12) else exit(1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Требуется Python 3.12+
    set /p install_python="📥 Хотите установить Python автоматически? (y/n): "
    if /i "%install_python%"=="y" (
        call :install_python
    ) else (
        echo 🚫 Установка Python отменена
        pause
        exit /b
    )
)
echo ✅ Успешно: Python 3.12+ обнаружен
exit /b

:: ========================================
:: Установка Python
:: ========================================
:install_python
echo 📥 [AUTO] Скачивание Python 3.12...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
if not exist "%PYTHON_INSTALLER%" (
    echo ❌ ОШИБКА: Не удалось скачать Python
    pause
    exit /b
)
echo 🛠️  [AUTO] Установка Python 3.12...
start /wait "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1
del "%PYTHON_INSTALLER%"
if errorlevel 1 (
    echo ❌ ОШИБКА: Установка Python завершилась с ошибкой
    pause
    exit /b
)
echo ✅ Успешно: Python 3.12 установлен
exit /b

:: ========================================
:: Создание .env файла
:: ========================================
:create_dotenv
echo.
echo 🔧 [2/5] Настройка окружения...
if exist "%DOT_ENV%" (
    echo 📄 Файл .env уже существует
) else (
    echo DEBUG=True              > "%DOT_ENV%"
    echo TELEGRAM_BOT_TOKEN=    >> "%DOT_ENV%"
    echo VK_BOT_TOKEN=          >> "%DOT_ENV%"
    echo FLASK_SECRET_KEY=      >> "%DOT_ENV%"
    echo INFO_PATH="databases/info.db" >> "%DOT_ENV%"
    echo USERS_PATH="databases/users.db" >> "%DOT_ENV%"
    echo API_URL=http://127.0.0.1:5000/api/message >> "%DOT_ENV%"
    echo 📝 Создан новый файл .env
    notepad "%DOT_ENV%"
)
exit /b

:: ========================================
:: Создание виртуального окружения
:: ========================================
:create_venv
echo.
echo 🌱 [3/5] Виртуальное окружение...
if exist "%VENV_DIR%" (
    echo 📁 Виртуальное окружение уже существует
) else (
    python -m venv "%VENV_DIR%"
    echo ✅ Виртуальное окружение создано
)
exit /b

:: ========================================
:: Установка зависимостей
:: ========================================
:install_dependencies
echo.
echo 📦 [4/5] Установка зависимостей...
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r "%REQUIREMENTS%"
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Не удалось установить зависимости
    pause
    exit /b
)
echo ✅ Зависимости успешно установлены
exit /b

:: ========================================
:: Активация виртуального окружения
:: ========================================
:activate_venv
echo.
echo 🔌 [5/5] Активация окружения...
call "%VENV_DIR%\Scripts\activate.bat"
exit /b

:: ========================================
:: Установка xTunnel
:: ========================================
:setup_xtunnel
echo.
echo 🌐 Настройка xTunnel...
if not exist "%XTUNNEL_EXE%" (
    echo 📥 Скачивание xTunnel...
    powershell -Command "Invoke-WebRequest -Uri '%XTUNNEL_URL%' -OutFile '%PROJECT_ROOT%xtunnel.zip'"
    if not exist "%PROJECT_ROOT%xtunnel.zip" (
        echo ❌ Не удалось скачать xTunnel
        pause
        exit /b
    )
    echo 📦 Распаковка xTunnel...
    if not exist "%XTUNNEL_DIR%" mkdir "%XTUNNEL_DIR%"
    powershell -Command "Expand-Archive -Path '%PROJECT_ROOT%xtunnel.zip' -DestinationPath '%XTUNNEL_DIR%' -Force"
    del "%PROJECT_ROOT%xtunnel.zip"
    if not exist "%XTUNNEL_EXE%" (
        echo ❌ Ошибка распаковки xTunnel
        pause
        exit /b
    )
    echo ✅ xTunnel успешно установлен
)
exit /b
:: ========================================
:: Запуск xTunnel
:: ========================================
:start_xtunnel
echo 🔄 Попытка запустить xTunnel на порту 5000...
start "xTunnel" /B cmd /c "%XTUNNEL_EXE% 5000"
timeout /t 5 /nobreak >nul
tasklist | find /i "xTunnel.exe" >nul
if %errorlevel% neq 0 (
    echo ❌ xTunnel не запустился. Требуется регистрация.
    start "" "https://cabinet.xtunnel.ru/"
    :get_key
    set "XTUNNEL_KEY="
    set /p XTUNNEL_KEY="🔑 Введите ключ регистрации xTunnel: "
    if "!XTUNNEL_KEY!"=="" (
        echo ❌ Ключ не может быть пустым
        goto get_key
    )
    echo 🛠️ Запуск xTunnel с ключом...
    start "xTunnel" /B cmd /c "%XTUNNEL_EXE% -k !XTUNNEL_KEY! 5000"
    timeout /t 5 /nobreak >nul
    tasklist | find /i "xTunnel.exe" >nul
    if %errorlevel% neq 0 (
        echo ❌ Не удалось запустить xTunnel с ключом
        pause
        exit /b
    )
)
echo ✅ xTunnel успешно запущен на порту 5000
exit /b

:: ========================================
:: Запуск компонентов
:: ========================================
:run_components
cls
echo.
echo ╔════════════════════════════════════╗
echo ║  🚀 Запуск компонентов системы     ║
echo ╚════════════════════════════════════╝
echo.
echo 🌐 Запуск Flask сервера...
start "Flask Server" /B cmd /c "python api\api.py"
echo 📨 Запуск Telegram бота...
start "Telegram Bot" /B cmd /c "python clients\telegram.py"
echo 🔵 Запуск VK бота...
start "VK Bot" /B cmd /c "python clients\vk.py"
echo.
echo ✅ Все компоненты запущены в фоновом режиме
echo .
:: Запуск сервера
call :start_xtunnel
echo 🛑 Для остановки закройте это окно
echo ══════════════════════════════════════
pause
exit /b