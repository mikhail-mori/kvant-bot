import os
import vk_api
import json
import requests
import logging
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s VK>> %(levelname)s %(message)s",
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Инициализация VK API
vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
vk = vk_session.get_api()
upload = VkUpload(vk_session)
longpoll = VkLongPoll(vk_session)

API_URL = "http://127.0.0.1:5000/api/message"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
user_messages: Dict[int, int] = {}

def send_to_api(user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Отправка данных в API"""
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise

def handle_media(content_type: str, file_path: str) -> str:
    """Загрузка медиафайлов"""
    full_path = os.path.join(BASE_DIR, file_path.lstrip("/"))
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {full_path}")

    try:
        if content_type == "photo":
            photo = upload.photo_messages(full_path)[0]
            return f"photo{photo['owner_id']}_{photo['id']}"
        elif content_type == "video":
            video = upload.video(full_path)['video']
            return f"video{video['owner_id']}_{video['id']}"
        elif content_type == "document":
            doc = upload.document_message(full_path, peer_id=0)
            return f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
        elif content_type == "audio":
            audio = upload.audio_message(full_path)
            return f"audio_message{audio['audio_message']['owner_id']}_{audio['audio_message']['id']}"
    except Exception as e:
        logger.error(f"Media upload failed: {str(e)}")
        raise

def convert_keyboard(api_keyboard: Dict[str, Any]) -> str:
    """Преобразование клавиатуры"""
    if not api_keyboard:
        return None

    keyboard = VkKeyboard(
        inline=api_keyboard.get("inline", False),
        one_time=api_keyboard.get("one_time", False) if not api_keyboard.get("inline", False) else False
    )
    color_map = {
        "primary": VkKeyboardColor.PRIMARY,
        "secondary": VkKeyboardColor.SECONDARY,
        "positive": VkKeyboardColor.POSITIVE,
        "negative": VkKeyboardColor.NEGATIVE
    }
    has_buttons_in_row = False

    for row in api_keyboard.get("buttons", []):
        for btn in row:
            action = btn.get("action", {})
            btn_type = action.get("type", "text")
            label = action.get("label", "")
            
            if btn_type == "text":
                color = color_map.get(action.get("color", "secondary"), VkKeyboardColor.SECONDARY)
                keyboard.add_button(label, color)
                has_buttons_in_row = True
            elif btn_type == "link":
                keyboard.add_openlink_button(label, action.get("link", ""))
                has_buttons_in_row = True
            elif btn_type == "callback":
                keyboard.add_callback_button(
                    label,
                    payload=json.dumps({"data": action.get("payload", "")})
                )
                has_buttons_in_row = True
        if has_buttons_in_row:
            keyboard.add_line()

    # Удаляем последнюю пустую строку, если она была добавлена
    if keyboard.lines and not keyboard.lines[-1]:
        keyboard.lines.pop()
    
    return keyboard.get_keyboard()

def process_event(event: VkEventType) -> Dict[str, Any]:
    """Обработка входящего события"""
    payload = {
        "user_id": event.user_id,
        "content_type": "text",
        "message_text": event.text
    }

    if event.attachments:
        for att in event.attachments:
            if att["type"] == "photo":
                payload.update({
                    "content_type": "photo",
                    "file_id": att["photo"]["id"]
                })
            elif att["type"] == "video":
                payload.update({
                    "content_type": "video",
                    "file_id": att["video"]["id"]
                })
            elif att["type"] == "doc":
                payload.update({
                    "content_type": "document",
                    "file_id": att["doc"]["id"]
                })
    
    return payload

def handle_api_response(user_id: int, response: Dict[str, Any]):
    """Обработка ответа API с поддержкой редактирования сообщений"""
    try:
        content_type = next(
            (ct for ct in ["photo", "video", "document", "audio", "geo"] if ct in response),
            None
        )

        attachment = None
        if content_type:
            if content_type == "geo":
                attachment = f"geo{response['geo']['latitude']}_{response['geo']['longitude']}"
            else:
                attachment = handle_media(content_type, response[content_type])

        # Получаем параметры для отправки/редактирования
        is_new = response.get('new', True)
        message_id = user_messages.get(user_id)

        # Подготовка параметров сообщения
        message_params = {
            "peer_id": user_id,
            "message": response.get("text", ""),
            "attachment": attachment,
            "keyboard": convert_keyboard(response.get("keyboard"))
        }

        if is_new or not message_id:
            # Отправка нового сообщения
            result = vk.messages.send(
                **message_params,
                random_id=get_random_id()
            )
            # Сохраняем ID нового сообщения
            user_messages[user_id] = result
        else:
            # Редактирование существующего сообщения
            message_params["message_id"] = message_id
            vk.messages.edit(**message_params)

    except vk_api.exceptions.ApiError as e:
        if e.code == 924:  # Сообщение слишком длинное для редактирования
            logger.warning(f"Message too long, sending new one. Error: {str(e)}")
            del user_messages[user_id]  # Удаляем старый ID
            handle_api_response(user_id, response)  # Рекурсивный вызов
        else:
            logger.error(f"API error: {str(e)}")
            send_fallback_message(user_id)
    except Exception as e:
        logger.error(f"Failed to handle API response: {str(e)}")
        send_fallback_message(user_id)

def send_fallback_message(user_id: int):
    """Отправка сообщения об ошибке"""
    try:
        vk.messages.send(
            user_id=user_id,
            message="⚠️ Произошла ошибка при обработке сообщения",
            random_id=0,
            keyboard=None
        )
    except Exception as e:
        logger.critical(f"Critical failure: {str(e)}")

def main():
    logger.info("🔵 VK Бот запущен")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                payload = process_event(event)
                api_response = send_to_api(event.user_id, payload)
                handle_api_response(event.user_id, api_response)
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {str(e)}")

if __name__ == "__main__":
    main()