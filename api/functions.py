import logging
import os
from database import use_database

# Настройка логов
logging.basicConfig(
    level=logging.DEBUG,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s",
    encoding='utf-8'
)

# Функции для логов
def debug(text: str): logging.debug(text)
def info(text: str): logging.info(text)
def warning(text: str): logging.warning(text)
def error(text: str): logging.error(text)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
INFO_URL = os.getenv("INFO_URL")
USERS_URL = os.getenv("USERS_URL")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_response(
    text: str = None,
    keyboard: dict = None,
    photo: str = None,
    error: str = None,
    status: int = 200,
) -> dict:
    """
    Формирует ответ для API.
    Args:
        text (str, optional): Отправляемый текст. Defaults to None.
        keyboard (dict, optional): Отправляемая клавиатура. Defaults to None.
        file (str, optional): Отправляемый файл. Defaults to None.
        error (str, optional): Сообщение об ошибке. Defaults to None.
        status (int, optional): HTTP-статус ответа. Defaults to 200.
    Returns:
        dict: Ответ для API.
    """
    response = {"status": status}
    if text:
        response["text"] = text
    if keyboard:
        response["keyboard"] = keyboard
    if photo:
        response["photo"] = photo
    if error:
        response["error"] = error
        debug(f"Бот подготовил ответ с ошибкой: {error}, статус={status}")
    else:
        debug(f"Бот подготовил ответ: текст={text}, клавиатура={keyboard is not None}, файл={photo is not None}")
    return response

def create_database() -> None:
    """
    Создаёт базы данных.
    """
    use_database(
        USERS_URL,
        """CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY,
            kvant TEXT,
            state TEXT)""",
    )
    use_database(
        INFO_URL,
        """CREATE TABLE IF NOT EXISTS kvant
           (kvant TEXT PRIMARY KEY,
            info_pic TEXT,
            schedule_pic TEXT,
            enrolment TEXT)""",
    )
    use_database(
        INFO_URL,
        """CREATE TABLE IF NOT EXISTS mentors
           (mentor TEXT PRIMARY KEY,
            kvant TEXT,
            info_pic TEXT)""",
    )
    use_database(
        INFO_URL,
        """CREATE TABLE IF NOT EXISTS mk
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        pic TEXT,
        info TEXT,
        link TEXT)"""
    )


def update_info(info_data: dict) -> None:
    """
    Обновляет информацию о Кванториуме в базе данных.
    Args:
        info_data (dict): Информация о Кванториуме.
    """
    # Обновление данных о квантах
    for kvant_name, kvant_data in info_data["kvantums"].items():
        use_database(
            INFO_URL,
            """INSERT OR REPLACE INTO kvant (kvant, info_pic, schedule_pic, enrolment)
               VALUES (:kvant, :info_pic, :schedule_pic, :enrolment)""",
            {
                "kvant": kvant_name,
                "info_pic": kvant_data.get("info_pic", ""),
                "schedule_pic": kvant_data.get("schedule_pic", ""),
                "enrolment": kvant_data.get("enrolment", ""),
            },
        )
    
    # Обновление данных о менторах
    for mentor_name, mentor_data in info_data["mentors"].items():
        use_database(
            INFO_URL,
            """INSERT OR REPLACE INTO mentors (mentor, kvant, info_pic)
               VALUES (:mentor, :kvant, :info_pic)""",
            {
                "mentor": mentor_name,
                "kvant": mentor_data["kvant"],
                "info_pic": mentor_data.get("info_pic", ""),
            },
        )
    
    # Обновление данных о MK (новая таблица)
    if "mk" in info_data:
        for mk_data in info_data["mk"]:
            use_database(
                INFO_URL,
                """INSERT OR REPLACE INTO mk (id, pic, info, link)
                   VALUES (:id, :pic, :info, :link)""",
                {
                    "id": mk_data.get("id", None),  # id может быть None для автоинкремента
                    "pic": mk_data.get("pic", ""),
                    "info": mk_data.get("info", ""),
                    "link": mk_data.get("link", ""),
                },
            )
    
    info("Информация о Кванториуме успешно обновлена в базе данных")


def get_info() -> dict:
    """
    Получает информацию о Кванториуме из базы данных.
    Returns:
        dict: Информация о Кванториуме.
    """
    # Получаем данные о квантах
    kvants = use_database(
        INFO_URL,
        "SELECT kvant, info_pic, schedule_pic, enrolment FROM kvant",
        fetchone=False,
    )
    kvant_data = {
            kvant[0]: {
                "info_pic": kvant[1],
                "schedule_pic": kvant[2],
                "enrolment": kvant[3],
            }for kvant in kvants
        } if kvants is not None else {}
    
    # Получаем данные о менторах
    mentors = use_database(
        INFO_URL,
        "SELECT mentor, kvant, info_pic FROM mentors",
        fetchone=False,
    )
    mentor_data = {
            mentor[0]: {"kvant": mentor[1], "info_pic": mentor[2]}
            for mentor in mentors
        } if mentors is not None else {}
    
    # Получаем данные о MK (новая таблица)
    mks = use_database(
        INFO_URL,
        "SELECT id, pic, info, link FROM mk",
        fetchone=False,
    )
    mk_data = [
            {
                "pic": mk[1],
                "info": mk[2],
                "link": mk[3],
            }
            for mk in mks
        ] if mks is not None else []
    
    return {
        "kvantums": kvant_data,
        "mentors": mentor_data,
        "mk": mk_data,
    }


def register_user(user_id: int) -> dict:
    """
    Регистрирует пользователя в боте.
    Args:
        user_id (int): Идентификатор пользователя.
    """
    info(f"Пользователь {user_id} зарегистрирован")
    use_database(
        USERS_URL,
        "INSERT INTO users(id, kvant, state) VALUES (:id, :kvant, :state)",
        {"id": user_id, "kvant": "", "state": "menu"},
    )
    return {"id": user_id, "kvant": "", "state": "menu"}


def get_kvant(user_id: int) -> str:
    """
    Получает текущий выбранный пользователем Квант.
    Args:
        user_id (int): Идентификатор пользователя.
    Returns:
        str: Текущий выбранный пользователем Квант.
    """
    kvant = use_database(
        USERS_URL, 
        "SELECT kvant FROM users WHERE id = :id", 
        {"id": user_id}
        )
    return kvant[0] if kvant is not None else register_user(user_id)["kvant"]


def set_kvant(user_id: int, kvant: str) -> None:
    """
    Настраивает текущий выбранный пользователем Квант.
    Args:
        user_id (int): Идентификатор пользователя.
        kvant (str): Текущий выбранный пользователем Квант.
    """
    use_database(
        USERS_URL, 
        "UPDATE users SET kvant = :kvant WHERE id = :id", 
        {"kvant": kvant, "id": user_id}
        )


def get_state(user_id: int) -> str:
    """
    Получает текущее положение пользователя в боте.
    Args:
        user_id (int): Идентификатор пользователя.
    Returns:
        str: Текущее положение пользователя в боте.
    """
    state = use_database(
        USERS_URL, 
        "SELECT state FROM users WHERE id = :id", 
        {"id": user_id}
        )
    return state[0] if state is not None else register_user(user_id)["state"]


def set_state(user_id: int, state: str) -> None:
    """
    Настраивает текущее положение пользователя в боте.
    Args:
        user_id (int): Идентификатор пользователя.
        state (str): Текущее положение пользователя в боте.
    """
    use_database(
        USERS_URL, 
        "UPDATE users SET state = :state WHERE id = :id", 
        {"state": state, "id": user_id}
        )