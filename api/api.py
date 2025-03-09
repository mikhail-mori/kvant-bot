from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from bcrypt import hashpw, gensalt, checkpw
from config import DevelopmentConfig
from dotenv import load_dotenv
from handlers import *
import os

load_dotenv()

password = os.getenv("PASSWORD")

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['SECRET_KEY'] = password
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Создаем папку для загрузок, если её нет

# Администраторы (в реальном проекте лучше хранить их в базе данных с хэшированием паролей)
ADMINS = {
    "admin": hashpw(password.encode(), gensalt()).decode()
}

def login_required(f):
    """
    Декоратор для проверки авторизации пользователя.
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Страница авторизации.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in ADMINS and checkpw(password.encode(), ADMINS[username].encode()):
            session["username"] = username
            return redirect(url_for("data_control"))
        else:
            flash("Неверное имя пользователя или пароль", "error")
    return render_template("index.html")

@app.route("/data-control", methods=["GET", "POST"])
@login_required
def data_control():
    """
    Страница управления данными.
    """
    if request.method == "POST":
        action = request.form.get("action")
        print(request.form, flush=True)
        
        # Добавление Кванта
        if action == "add_kvant":
            kvant_name = request.form.get("kvant_name")
            info_pic = request.form.get("info_pic")
            schedule_pic = request.form.get("schedule_pic")
            enrolment = request.form.get("enrolment")
            use_database(
                INFO_URL,
                """
                INSERT INTO kvant (kvant, info_pic, schedule_pic, enrolment)
                VALUES (:kvant, :info_pic, :schedule_pic, :enrolment)
                """,
                {"kvant": kvant_name, "info_pic": info_pic, "schedule_pic": schedule_pic, "enrolment": enrolment},
            )
            flash("Квант успешно добавлен!", "success")
        
        # Добавление Наставника
        elif action == "add_mentor":
            mentor_name = request.form.get("mentor_name")
            kvant = request.form.get("kvant")
            info_pic = request.form.get("info_pic")
            use_database(
                INFO_URL,
                """
                INSERT INTO mentors (mentor, kvant, info_pic)
                VALUES (:mentor, :kvant, :info_pic)
                """,
                {"mentor": mentor_name, "kvant": kvant, "info_pic": info_pic},
            )
            flash("Наставник успешно добавлен!", "success")
        
        # Добавление записи MK
        elif action == "add_mk":
            pic = request.form.get("info_pic")
            info = request.form.get("mk_info")
            link = request.form.get("link")
            use_database(
                INFO_URL,
                """
                INSERT INTO mk (pic, info, link)
                VALUES (:pic, :info, :link)
                """,
                {"pic": pic, "info": info, "link": link},
            )
            flash("Запись MK успешно добавлена!", "success")
        
        # Удаление Кванта
        elif action == "delete_kvant":
            kvant_name = request.form.get("kvant_name")
            use_database(
                INFO_URL,
                "DELETE FROM kvant WHERE kvant = :kvant",
                {"kvant": kvant_name},
            )
            flash("Квант успешно удален!", "success")
        
        # Удаление Наставника
        elif action == "delete_mentor":
            mentor_name = request.form.get("mentor_name")
            use_database(
                INFO_URL,
                "DELETE FROM mentors WHERE mentor = :mentor",
                {"mentor": mentor_name},
            )
            flash("Наставник успешно удален!", "success")
        
        # Удаление записи MK
        elif action == "delete_mk":
            mk_id = request.form.get("mk_index")
            use_database(
                INFO_URL,
                "DELETE FROM mk WHERE id = :id",
                {"id": mk_id},
            )
            flash("Запись MK успешно удалена!", "success")
        
        # Обновление Кванта
        elif action == "update_kvant":
            old_kvant_name = request.form.get("old_kvant_name")
            new_kvant_name = request.form.get("new_kvant_name")
            info_pic = request.form.get("info_pic")
            schedule_pic = request.form.get("schedule_pic")
            enrolment = request.form.get("enrolment")
            use_database(
                INFO_URL,
                """
                UPDATE kvant
                SET kvant = :new_kvant, info_pic = :info_pic, schedule_pic = :schedule_pic, enrolment = :enrolment
                WHERE kvant = :old_kvant
                """,
                {"new_kvant": new_kvant_name, "info_pic": info_pic, "schedule_pic": schedule_pic, "enrolment": enrolment, "old_kvant": old_kvant_name},
            )
            flash("Квант успешно обновлен!", "success")
        
        # Обновление Наставника
        elif action == "update_mentor":
            old_mentor_name = request.form.get("old_mentor_name")
            new_mentor_name = request.form.get("new_mentor_name")
            kvant = request.form.get("kvant")
            info_pic = request.form.get("info_pic")
            use_database(
                INFO_URL,
                """
                UPDATE mentors
                SET mentor = :new_mentor, kvant = :kvant, info_pic = :info_pic
                WHERE mentor = :old_mentor
                """,
                {"new_mentor": new_mentor_name, "kvant": kvant, "info_pic": info_pic, "old_mentor": old_mentor_name},
            )
            flash("Наставник успешно обновлен!", "success")
        
        # Обновление записи MK
        elif action == "update_mk":
            mk_id = request.form.get("mk_index")
            pic = request.form.get("info_pic")
            info = request.form.get("mk_info_edit")
            link = request.form.get("mk_link_edit")
            use_database(
                INFO_URL,
                """
                UPDATE mk
                SET pic = :pic, info = :info, link = :link
                WHERE id = :id
                """,
                {"pic": pic, "info": info, "link": link, "id": mk_id},
            )
            flash("Запись MK успешно обновлена!", "success")
        
        # Загрузка изображения
        elif action == "upload_image":
            if 'file' not in request.files:
                flash("Файл не выбран", "error")
                return redirect(url_for("data_control"))
        
            file = request.files['file']
            if file.content_length > MAX_FILE_SIZE:
                flash("Файл слишком большой", "error")
                return redirect(url_for("data_control"))
        
            if not allowed_file(file.filename):
                flash("Недопустимый тип файла", "error")
                return redirect(url_for("data_control"))
            
            if file.filename == "":
                flash("Файл не выбран", "error")
                return redirect(url_for("data_control"))
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            return jsonify({"file_path": f"/static/uploads/{file.filename}"})
    
    # Получение данных из базы данных
    kvants = use_database(INFO_URL, "SELECT * FROM kvant", fetchone=False) or []
    mentors = use_database(INFO_URL, "SELECT * FROM mentors", fetchone=False) or []
    mks = use_database(INFO_URL, "SELECT * FROM mk", fetchone=False) or []
    
    return render_template("data-control.html", kvants=kvants, mentors=mentors, mks=mks)

@app.route("/logout")
def logout():
    """
    Выход из системы.
    """
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route('/api/message', methods=['POST'])
def handle_message():
    """
    Обрабатывает входящие сообщения через API.
    Ожидает JSON с полями: user_id, message, user_info.
    """
    try:
        # Получаем данные из POST-запроса
        data = request.json
        user_id = data.get('user_id')
        print(user_id)
        content_type = data.get('content_type')
        if content_type == 'text': message = data.get('message_text')
        elif content_type == 'callback': message = data.get("callback_data")
        else: message = "Начать"

        if not user_id or not message:
            return jsonify({"error": "Missing required fields: user_id or message"}), 400

        # Получаем основную информацию
        state = get_state(user_id)
        kvant = get_kvant(user_id)
        info = get_info()

        # Обработка команд
        if message in ('Начать', "/start") or message.startswith('Вернуться'):
            state, kvant = handle_back(user_id, message)
            set_state(user_id, state)
            set_kvant(user_id, kvant)

        match state:
            case 'menu':
                ################
                # Главное меню #
                ################
                match message:
                    case 'Начать' | 'Вернуться в меню' | "/start":
                        response = handle_main_menu(user_id)
                    case 'Записаться на занятия':
                        response = handle_enrolment(user_id, info)
                    case 'Записаться на мастеркласс':
                        response = handle_mk(user_id, info)
                    case 'Информация о Квантумах':
                        response = handle_info(user_id, info)
                    case _:
                        response = {"text": "Неизвестная команда"}

            case 'info':
                if kvant is None and message in tuple(info['kvantums']):
                    kvant = message
                    set_kvant(user_id, kvant)
                if message in tuple(info["mentors"]):
                    response = handle_pedagogs(user_id, info, message)
                elif message == 'Записаться':
                    set_state(user_id, 'enrolment')
                    response = handle_enrolment(user_id, info, kvant)
                else:
                    response = handle_info(user_id, info, kvant)

            case 'enrolment':
                if kvant is None and message in tuple(info['kvantums']):
                    kvant = message
                    set_kvant(user_id, kvant)
                if message in ("Информация о Квантуме", "Вернуться к Квантуму"):
                    response = handle_info(user_id, info, kvant, from_enrolment=True)
                elif message in tuple(info["mentors"]):
                    response = handle_pedagogs(user_id, info, message,)
                else: 
                    response = handle_enrolment(user_id, info, kvant)

            case 'mk':
                if kvant is not None and kvant.isdigit():
                    if message in ("<", "&lt;"):
                        if int(kvant) - 1 <= -1: response = handle_mk(user_id, info, len(info['mk'])-1)
                        else: response = handle_mk(user_id, info, int(kvant)-1)

                    elif message in (">", "&gt;"):
                        if int(kvant) + 1 >= len(info['mk']): response = handle_mk(user_id, info, 0)
                        else: response = handle_mk(user_id, info, int(kvant)+1)

                    else:
                        warning(f"Мастеркласс был не обработан! Полученное сообщение: {message}")
                        set_state(user_id, 'menu')
                        response = handle_main_menu(user_id)

                else: response = handle_mk(user_id, info)
            
            case _:
                set_state(user_id, 'menu')
                response = handle_main_menu(user_id)

        # Возвращаем ответ клиенту
        return jsonify(response), 200

    except Exception as e:
        error(f"Произошла ошибка: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == '__main__':
    create_database()
    # Запуск сервера Flask
    print("🌐 Flask сервер запущен")
    app.run(host='0.0.0.0', port=5000, debug=False)