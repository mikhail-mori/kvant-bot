import time
import os
from functions import *
from keyboards import (
    get_enrolment_keyboard,
    get_kvantums_keyboard,
    get_main_keyboard,
    get_mentors_keyboard,
    get_mk_keyboard,
    get_return_from_mentors_keyboard,
    get_return_to_main_menu_keyboard,
)
from database import use_database

# Глобальные переменные
admins = (588882091,)

# Обработчик возвращения
def handle_back(user_id: int, message: str) -> tuple:
    """Обрабатывает запрос на Вернутся ... .

    Args:
        user_id (int): Идетификатор пользователя.
        message (str): Сообщение, начинающееся с Вернутся или Начать.

    Returns:
        tuple: Состояние и квант пользователя, которое нужно поставить.
    """
    match message:
        case 'Начать' | 'Вернуться в меню':
            state = 'menu'
            kvant = None
        case 'Вернуться к выбору Квантов':
            state = get_state(user_id)
            kvant = None
        case 'Вернуться к записи':
            state = 'enrolment'
            kvant = get_kvant(user_id)
        case 'Вернуться к Квантуму':
            state = get_state(user_id)
            kvant = get_kvant(user_id)
        case _:
            state = 'menu'
            kvant = None

    return state, kvant

################
# Главное меню #
################

def handle_main_menu(user_id: int) -> dict:
    """Отправляет главное меню.
    Args:
        user_id (int): Идентификатор пользователя.
    Returns:
        dict: Ответ для API.
    """
    debug(f"{user_id} попал в хендлер главного меню")
    return send_response(
        text="Здравствуйте, чем можем помочь?",
        keyboard=get_main_keyboard(),
    )


def handle_enrolment(user_id: int, info: dict, kvant: str | None = None) -> dict:
    """Отправляет ссылку на регистрацию на занятия.
    Args:
        user_id (int): Идентификатор пользователя.
        info (dict): Информация о Кванториуме.
    Returns:
        dict: Ответ для API.
    """
    debug(f"{user_id} попал в хендлер записи на занятия")
    match kvant:
        case None:
            keyboard = get_kvantums_keyboard(info['kvantums'])
            set_state(user_id, 'enrolment')
            return send_response(
                text='Выберите Квант:',
                keyboard=keyboard
            )
        case kvant:
            keyboard = get_enrolment_keyboard(info['kvantums'][kvant]['enrolment'])
            return send_response(
                text=f"Расписание занятий {kvant}а.",
                keyboard=keyboard,
                photo=info['kvantums'][kvant]['schedule_pic']
            )



def handle_info(user_id: int, info: dict, kvant: str | None = None, from_enrolment: bool = False) -> dict:
    """Отправляет информацию о Квантумах.
    Args:
        user_id (int): Идентификатор пользователя.
        info (dict): Информация о Кванториуме.
        kvant (str | None, optional): Квант, о котором хочет узнать пользователь.
        from_enrolment (bool): Открыта ли панель из зоны записи?
    Returns:
        dict: Ответ для API.
    """
    debug(f"{user_id} попал в хендлер информации о квантумах")
    match kvant:
        case None:
            keyboard = get_kvantums_keyboard(info["kvantums"])
            set_state(user_id, 'info')
            return send_response(
                text="О каком Квантуме Вы хотите узнать?",
                keyboard=keyboard
            )
        case kvant:
            set_kvant(user_id, kvant)
            mentors = []
            for mentor in info['mentors']:
                if info['mentors'][mentor]['kvant'] == kvant:
                    mentors.append(str(mentor))
            keyboard = get_mentors_keyboard(mentors, from_enrolment)
            return send_response(
                text=f"Информация о {kvant}е:",
                keyboard=keyboard,
                photo=info['kvantums'][kvant]['info_pic']
            )


def handle_pedagogs(
    user_id: int, info: dict, mentor: str
) -> dict:
    """Отправляет информацию о педагогах.
    Args:
        user_id (int): Идентификатор пользователя.
        info (dict): Информация о Кванториуме.
        mentor (str): Преподаватель, о котором хочет узнать пользователь.
    Returns:
        dict: Ответ для API.
    """
    debug(f"{user_id} попал в хендлер педагогов")
    photo = str(info["mentors"][mentor]["info_pic"])
    keyboard = get_return_from_mentors_keyboard()
    return send_response(
        text=f"Информация о наставнике с ФИО {mentor}",
        keyboard=keyboard,
        photo=photo
    )

def handle_mk(
        user_id: int, info: dict, mk_id: int = 0
) -> dict:
    """Отправляет информацию о мастерклассах.
    Args:
        user_id (int): Идентификатор пользователя.
        info (dict): Информация о Кванториуме.
        mk_id (int): Идентификатор мастеркласса в базе данных.
    Returns:
        dict: Ответ для API.
    """
    if len(info['mk']) == 0: # Если Мастерклассов нету
        keyboard = get_return_to_main_menu_keyboard()
        return send_response(
            text="К сожалению пока нету Мастерклассов, загляните сюда позже!",
            keyboard=keyboard
        )
    
    set_state(user_id, "mk")
    set_kvant(user_id, str(mk_id))
    keyboard = get_mk_keyboard(info["mk"][mk_id]["link"])
    return send_response(
        text=info["mk"][mk_id]["info"],
        keyboard=keyboard,
        photo=info['mk'][mk_id]["pic"]
    )