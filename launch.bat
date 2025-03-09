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
set "LOG_FILE=%PROJECT_ROOT%app.log"
set "FLASK_PORT=5000"

:: Настройки xTunnel
set "XTUNNEL_DIR=%PROJECT_ROOT%xTunnel"
set "XTUNNEL_EXE=%XTUNNEL_DIR%\xTunnel.exe"
set "XTUNNEL_URL=https://files.xtunnel.ru/xtunnel/1.0.14/xTunnel.win-x64.1.0.14.zip"
set "XTUNNEL_PORT=5000"

:: Главное меню
:main
call :check_status
cls
echo.
echo ╔═══════════════════════════════════════════╗
echo ║  🚀 Кванториум Бот - Система управления   ║
echo ╚═══════════════════════════════════════════╝
echo.
echo Текущий статус: !project_status!
echo.
echo 1. 🛠️  Установить зависимости и запустить
echo 2. ⚡ Только запустить
echo 3. 🔄 Перезапустить всё
echo 4. 🔍 Просмотреть последние ошибки логов
echo 5. 🚪 Выход
echo.
set /p choice="👉 Выберите действие: "
if "%choice%"=="1" goto full_install
if "%choice%"=="2" goto run_only
if "%choice%"=="3" goto restart_all
if "%choice%"=="4" goto view_errors
if "%choice%"=="5" exit /b
goto main

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
echo 🔧 Создание .env файла...
if not exist "%DOT_ENV%" (
    echo DEBUG=True> "%DOT_ENV%"
    echo TELEGRAM_TOKEN=>> "%DOT_ENV%"
    echo VK_TOKEN=>> "%DOT_ENV%"
    echo PASSWORD=>> "%DOT_ENV%"
    echo INFO_URL=sqlite:///databases/info.db>> "%DOT_ENV%"
    echo USERS_URL=sqlite:///databases/users.db>> "%DOT_ENV%"
)
echo ✅ Файл .env готов
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
goto main

:: Настройка xTunnel
:setup_xtunnel
:: Проверка наличия xTunnel
if not exist "%XTUNNEL_EXE%" (
    echo 🚀 xTunnel не найден, начинаем установку...
    call :install_xtunnel || (
        echo ❌ Установка xTunnel прервана
        exit /b 1
    )
)

:: Попытка запуска
echo ▶ Запуск xTunnel на порту %XTUNNEL_PORT%...
start "" /B "%XTUNNEL_EXE%" -p %XTUNNEL_PORT%

:: Проверка запуска
set "max_attempts=5"
for /L %%i in (1,1,%max_attempts%) do (
    timeout /T 2 /NOBREAK >nul
    tasklist /FI "IMAGENAME eq xTunnel.exe" 2>nul | find /I "xTunnel.exe" >nul
    if !errorlevel! equ 0 (
        echo ✅ xTunnel успешно запущен
        exit /b 0
    )
)

:: Если не запустился - запрос ключа
echo ❗ xTunnel не активирован!
echo 🔑 Перейдите на https://cabinet.xtunnel.ru/ для получения ключа
set /p "activation_key=Введите ключ активации: "

:: Перезапуск с ключом
taskkill /F /IM xTunnel.exe >nul 2>&1
echo ▶ Перезапуск с ключом...
start "" /B "%XTUNNEL_EXE%" -k %activation_key% -p %XTUNNEL_PORT%

:: Финальная проверка
timeout /T 5 /NOBREAK >nul
tasklist /FI "IMAGENAME eq xTunnel.exe" 2>nul | find /I "xTunnel.exe" >nul
if !errorlevel! neq 0 (
    echo ❌ Не удалось запустить xTunnel
    echo 🛑 Прерывание работы
    exit /b 1
)
exit /b 0

:: Установка xTunnel
:install_xtunnel
echo 📥 Скачивание xTunnel...
set "zip_file=%TEMP%\xTunnel.zip"
powershell -Command "Invoke-WebRequest -Uri '%XTUNNEL_URL%' -OutFile '%zip_file%'"
if %errorlevel% neq 0 (
    echo ❌ Ошибка скачивания
    del /Q "%zip_file%" 2>nul
    exit /b 1
)

echo 📦 Распаковка...
if not exist "%XTUNNEL_DIR%" mkdir "%XTUNNEL_DIR%"
tar -xf "%zip_file%" -C "%XTUNNEL_DIR%" --overwrite
if %errorlevel% neq 0 (
    echo ❌ Ошибка распаковки
    del /Q "%zip_file%"
    exit /b 1
)

del /Q "%zip_file%"
echo ✅ xTunnel установлен в %XTUNNEL_DIR%
exit /b 0