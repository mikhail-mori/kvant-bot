@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Основные настройки проекта
set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%venv"
set "REQUIREMENTS=%PROJECT_ROOT%requirements.txt"
set "DOT_ENV=%PROJECT_ROOT%.env"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"
set "LOG_DIR=%PROJECT_ROOT%logs"
set "LOG_FILE=%LOG_DIR%\app.log"
set "FLASK_PORT=5000"
set "admin_url="

:: Настройки xTunnel
set "XTUNNEL_DIR=%PROJECT_ROOT%xTunnel"
set "XTUNNEL_EXE=%XTUNNEL_DIR%\xTunnel.exe"
set "XTUNNEL_URL=https://files.xtunnel.ru/xtunnel/1.0.14/xTunnel.win-x64.1.0.14.zip"
set "XTUNNEL_LOG=%TEMP%\xtunnel_%RANDOM%.log"

:: Главное меню
:main
call :check_status
cls
echo.
echo ╔═══════════════════════════════════════════╗
echo ║  🚀 Кванториум Бот - Система управления   ║
echo ╚═══════════════════════════════════════════╝
echo.
echo Текущий статус: !project_status! !admin_url!
echo.
echo 1. 🛠️  Установить зависимости и запустить (Первый запуск)
echo 2. ⚡ Только запустить
echo 3. 🔄 Перезапустить
echo 4. 🔍 Просмотреть последние ошибки
echo 5. 🚪 Выход
echo.
set /p choice="👉 Выберите действие: "
if "%choice%"=="1" goto full_install
if "%choice%"=="2" goto run_only
if "%choice%"=="3" goto restart_all
if "%choice%"=="4" goto view_errors
if "%choice%"=="5" exit /b
goto main

:: Функция просмотра последних строк файла
:tail
setlocal
set "file=%~1"
set "lines=%~2"
if "%lines%"=="" set lines=5
powershell -nologo -noprofile -command "Get-Content '%file%' | Select-Object -Last %lines%"
exit /b

:: Проверка статуса по порту
:check_status
set "project_status=Не запущен"
netstat -ano | findstr /R /C:"TCP .*:%FLASK_PORT% .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 set "project_status=Запущен"
exit /b

:: Полная установка
:full_install
call :check_python
call :create_dotenv
call :create_venv
call :install_dependencies
call :setup_xtunnel
goto run_components

:: Только запуск
:run_only
call :check_python
call :activate_venv
call :setup_xtunnel
goto run_components

:: Перезапуск всех компонентов
:restart_all
echo 🔄 [Перезапуск всех компонентов...]
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM xTunnel.exe >nul 2>&1
timeout /T 2 /NOBREAK > nul
goto run_components

:: Просмотр последних ошибок логов
:view_errors
echo 🔍 [Просмотр ошибок логов...]
findstr /C:"ERROR" "%LOG_FILE%"
pause
goto main

:: Проверка Python
:check_python
echo.
echo 🔍 Проверка Python...
python -c "import sys; exit(0) if sys.version_info >= (3, 12) else exit(1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Требуется Python 3.12+
    set /p install_python="Установить автоматически? (y/n): "
    if /i "!install_python!"=="y" call :install_python
    if /i not "!install_python!"=="y" exit /b
)
exit /b

:: Установка Python
:install_python
echo 📥 Скачивание Python...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
start /wait "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1
del "%PYTHON_INSTALLER%"
exit /b

:: Создание .env файла
:create_dotenv
echo.
echo 🔧 [2/5] Настройка окружения...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%LOG_FILE%" (
    echo Logs have been created > "%LOG_FILE%"
    echo 📝 Создан новый файл логов
)
if exist "%DOT_ENV%" (
    echo 📄 Файл .env уже существует
) else (
    echo.
    echo 🔧 [2/5] Ввод параметров окружения...
    set /p flask_secret_key="Введите пароль: "
    set /p telegram_bot_token="Введите токен телеграм бота: "
    set /p vk_bot_token="Введите токен вк бота: "
    echo DEBUG=False              > "%DOT_ENV%"
    echo PASSWORD="!flask_secret_key!" >> "%DOT_ENV%"
    echo TELEGRAM_TOKEN="!telegram_bot_token!" >> "%DOT_ENV%"
    echo VK_TOKEN="!vk_bot_token!" >> "%DOT_ENV%"
    echo INFO_URL="sqlite:///databases/info.db" >> "%DOT_ENV%"
    echo USERS_URL="sqlite:///databases/users.db" >> "%DOT_ENV%"
    echo ✅ Успешно: Параметры окружения настроены
)
exit /b

:: Создание виртуального окружения
:create_venv
echo.
echo 🌱 Создание виртуального окружения...
if not exist "%VENV_DIR%" python -m venv "%VENV_DIR%"
exit /b

:: Установка зависимостей
:install_dependencies
echo.
echo 📦 Установка зависимостей...
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r "%REQUIREMENTS%"
exit /b

:: Активация виртуального окружения
:activate_venv
echo.
echo 🔌 Активация окружения...
call "%VENV_DIR%\Scripts\activate.bat"
exit /b

:: Настройка xTunnel (исправленная версия)
:setup_xtunnel
echo.
:: Проверка наличия xTunnel
if not exist "%XTUNNEL_EXE%" (
    echo 🚀 xTunnel не найден, начинаем установку...
    call :install_xtunnel || (
        echo ❌ Установка xTunnel прервана
        exit /b 1
    )
)

:: Проверка статуса регистрации
echo ▶ Проверка статуса xTunnel...
"%XTUNNEL_EXE%" status > "%XTUNNEL_LOG%" 2>&1
findstr /C:"Status: Registered" "%XTUNNEL_LOG%" >nul
if %errorlevel% neq 0 (
    echo ❗ Требуется активация xTunnel!
    echo 🔑 Перейдите на https://cabinet.xtunnel.ru/ для получения ключа
    set "activation_key="
    set /p "activation_key=Введите ключ активации: "
    
    :: Проверка ввода ключа
    if "!activation_key!"=="" (
        echo ❌ Ключ активации не введен!
        exit /b 1
    )
    
    :: Выполнение активации с кавычками
    echo ▶ Регистрация xTunnel...
    "%XTUNNEL_EXE%" register "!activation_key!" > "%XTUNNEL_LOG%" 2>&1
    
    :: Проверка результата
    findstr /C:"Registration completed successfully" "%XTUNNEL_LOG%" >nul
    if %errorlevel% neq 0 (
        echo ❌ Ошибка активации. Логи:
        type "%XTUNNEL_LOG%"
        del "%XTUNNEL_LOG%"
        pause
        exit /b 1
    )
    echo ✅ Успешная активация xTunnel
)

:: Запуск туннеля
echo ▶ Запуск туннеля на порту %FLASK_PORT%...
start "xTunnel" /B "%XTUNNEL_EXE%" http %FLASK_PORT% > "%XTUNNEL_LOG%" 2>&1

:: Ожидание инициализации
echo ⏳ Ожидание публикации (15 секунд)...
timeout /T 15 >nul

:: Извлечение URL
set "admin_url="
for /f "tokens=*" %%a in ('findstr /R /C:"Public address: http" "%XTUNNEL_LOG%"') do (
    set "line=%%a"
    set "line=!line:Public address: =!"
    set "admin_url=!line: =!"
)

if defined admin_url (
    echo ✅ Туннель активирован: !admin_url!
    del "%XTUNNEL_LOG%" >nul 2>&1
) else (
    echo ❌ Ошибка получения URL
    echo Последние строки лога:
    type "%XTUNNEL_LOG%"
    exit /b 1
)
exit /b 0

:: Запуск компонентов
:run_components
call :check_status
if "!project_status!"=="Запущен" (
    echo ❗ Проект уже запущен
    timeout /T 2 /NOBREAK >nul
    goto main
)
echo 🌐 Запуск сервера и ботов...
start "" /B python api\api.py
start "" /B python clients\telegram.py
start "" /B python clients\vk.py
echo ✅ Компоненты запущены в фоне
timeout /T 2 /NOBREAK >nul
cls
goto main