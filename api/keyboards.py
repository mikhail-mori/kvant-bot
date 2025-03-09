################
# Главное меню #
################

def get_main_keyboard() -> dict:
    """
    Создаёт клавиатуру для главного меню.
    Returns:
        dict: Клавиатура с главным меню.
    """
    return {
        "one_time": True,
        "inline": True,
        "buttons": [
            [
                {"action": {"type": "text", "label": "Записаться на занятия"}, "color": "primary"},
                {"action": {"type": "text", "label": "Записаться на мастеркласс"}, "color": "primary"},
            ],
            [
                {"action": {"type": "text", "label": "Информация о Квантумах"}, "color": "primary"},
            ],
        ],
    }


def get_return_to_main_menu_keyboard() -> dict:
    return {
        "one_time": True,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]            
        ]
    }


def get_kvantums_keyboard(kvantums: list) -> dict:
    """
    Создаёт клавиатуру со списком Квантов.
    Args:
        kvantums (list): Кванты, которые есть.
        is_info (bool | None, optional): Добавлять ли кнопку "Информация о квантумах" или нет?
    Returns:
        dict: Клавиатура со списком Квантов.
    """
    keyboard = {"one_time": False, "inline": True, "buttons": []}
    row = []

    for i, kvant in enumerate(kvantums):
        row.append({"action": {"type": "text", "label": kvant}, "color": "primary"})
        if (i + 1) % 2 == 0 or i + 1 == len(kvantums):
            keyboard["buttons"].append(row)
            row = []

    keyboard["buttons"].append(
        [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]
    )
    return keyboard


def get_enrolment_keyboard(link: str) -> dict:
    """
    Создаёт клавиатуру с ссылкой на запись, информацией о Квантуме и кнопками возврата.
    Args:
        link (str): Ссылка на запись.
    Returns:
        dict: Клавиатура с ссылкой на запись, информацией о Квантуме и кнопками возврата.
    """
    return {
        "one_time": True,
        "inline": True,
        "buttons": [
            [{"action": {"type": "link", "label": "Записаться", "link": link}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Информация о Квантуме"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Вернуться к выбору Квантов"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]            
        ]
    }


def get_mentors_keyboard(mentors: list, from_enrolment: bool = False) -> dict:
    """
    Создаёт клавиатуру со списком наставников Кванта.
    Args:
        mentors (list): Список наставников Кванта.
    Returns:
        dict: Клавиатура со списком наставников Кванта.
    """
    keyboard = {"one_time": False, "inline": True, "buttons": []}
    row = []

    for i, mentor in enumerate(mentors):
        row.append({"action": {"type": "text", "label": mentor}, "color": "primary"})
        if (i + 1) % 2 == 0 or i + 1 == len(mentors):
            keyboard["buttons"].append(row)
            row = []

    if not from_enrolment:
        keyboard["buttons"].append(
            [{"action": {"type": "text", "label": "Записаться"}, "color": "primary"}]
        )
        keyboard["buttons"].append(
            [{"action": {"type": "text", "label": "Вернуться к выбору Квантов"}, "color": "secondary"}]
        )
    else:
        keyboard["buttons"].append(
        [{"action": {"type": "text", "label": "Вернуться к записи"}, "color": "secondary"}]
    )
    keyboard["buttons"].append(
        [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]
    )
    return keyboard


def get_return_from_mentors_keyboard() -> dict:
    """
    Создаёт клавиатуру с кнопкой Вернуться в меню и Вернутся к Квантуму для точки информации о педагогах.
    Returns:
        dict: Клавиатура с кнопкой Вернуться в меню.
    """
    return {
        "one_time": True,
        "inline": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Вернуться к Квантуму"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]
        ],
    }

def get_mk_keyboard(link: str):
    """
    Создаёт клавиатуру с кнопкой Записаться, стрелочками и возвратом в меню.
    Returns:
        dict: Клавиатура с кнопкой Вернуться в меню.
    """
    return {
        "one_time": False,
        "inline": True,
        "buttons": [
            [{"action": {"type": "link", "label": "Записаться", "link": link}, "color": "primary"}],
            [{"action": {"type": "text", "label": "<"}, "color": "primary"},
             {"action": {"type": "text", "label": ">"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Вернуться в меню"}, "color": "secondary"}]
        ]
    }
