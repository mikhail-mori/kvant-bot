import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAudio,
    InputMediaDocument,
    FSInputFile
)
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
import asyncio
import requests
import logging

load_dotenv()

# Инициализация логгера
logging.basicConfig(
    level=logging.DEBUG,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s TELEGRAM>> %(levelname)s %(message)s",
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Инициализация Telegram бота
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# URL API
API_URL = "http://127.0.0.1:5000/api/message"

# Корневая директория проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Словарь для хранения message_id последних сообщений пользователей
user_messages = {}

async def send_to_api(user_id: int, content_type: str, **kwargs) -> dict:
    """Универсальная функция для отправки данных в API"""
    payload = {
        "user_id": user_id,
        "content_type": content_type,
        **kwargs
    }
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        raise

async def handle_api_response(
    user_id: int,
    api_response: dict,
    message_id: int = None,
    chat_id: int = None
):
    """Обработка всех типов контента из API"""
    try:
        content_types = {
            'photo': {'method': 'send_photo', 'media_type': InputMediaPhoto},
            'video': {'method': 'send_video', 'media_type': InputMediaVideo},
            'document': {'method': 'send_document', 'media_type': InputMediaDocument},
            'audio': {'method': 'send_audio', 'media_type': InputMediaAudio},
            'voice': {'method': 'send_voice', 'media_type': None},
            'video_note': {'method': 'send_video_note', 'media_type': None},
            'geo': {'method': 'send_location', 'media_type': None},
            'poll': {'method': 'send_poll', 'media_type': None}
        }

        # Определяем тип контента
        content_type = next(
            (ct for ct in content_types if api_response.get(ct)),
            None
        )
        text = api_response.get("text", "")
        keyboard = convert_keyboard_to_telegram_format(api_response.get("keyboard"))

        media_data = None
        media_file = None
        media_method = None
        edit_media_type = None

        if content_type:
            media_data = api_response[content_type]
            media_method = content_types[content_type]['method']
            edit_media_type = content_types[content_type]['media_type']

        # Загрузка медиа если требуется
        if content_type in ['photo', 'video', 'document', 'audio']:
            media_file = await upload_media(media_data, content_type)

        # Логика редактирования/отправки
        if message_id and chat_id:
            if media_method and edit_media_type:
                # Редактирование медиа
                media = edit_media_type(
                    media=media_file or media_data,
                    caption=text if content_type != 'audio' else None
                )
                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=media,
                    reply_markup=keyboard
                )
                return
            elif content_type == 'geo':
                await bot.edit_message_live_location(
                    chat_id=chat_id,
                    message_id=message_id,
                    latitude=media_data['latitude'],
                    longitude=media_data['longitude'],
                    reply_markup=keyboard
                )
                return
            else:
                # Удаление старого сообщения при смене типа
                await bot.delete_message(chat_id, message_id)

        # Отправка нового сообщения
        kwargs = {
            'chat_id': user_id,
            'reply_markup': keyboard
        }

        if content_type:
            if content_type == 'geo':
                kwargs.update({
                    'latitude': media_data['latitude'],
                    'longitude': media_data['longitude']
                })
            elif content_type == 'poll':
                kwargs.update({
                    'question': media_data['question'],
                    'options': media_data['options'],
                    'is_anonymous': media_data.get('is_anonymous', False)
                })
            else:
                kwargs[content_type] = media_file or media_data
                if text and content_type in ['photo', 'video', 'document']:
                    kwargs['caption'] = text

            sent_message = await getattr(bot, media_method)(**kwargs)
        else:
            sent_message = await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard
            )

        user_messages[user_id] = sent_message.message_id

    except Exception as e:
        logger.error(f"Error handling API response: {str(e)}")
        await bot.send_message(user_id, f"⚠️ Произошла ошибка: {str(e)}")

async def upload_media(file_path: str, content_type: str) -> str:
    """Универсальная загрузка медиафайлов с правильным получением file_id"""
    try:
        full_path = os.path.join(BASE_DIR, file_path.lstrip("/"))
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        methods = {
            'photo': (bot.send_photo, "photo"),
            'video': (bot.send_video, "video"),
            'document': (bot.send_document, "document"),
            'audio': (bot.send_audio, "audio"),
            'voice': (bot.send_voice, "voice")
        }

        if content_type not in methods:
            raise ValueError(f"Unsupported content type: {content_type}")

        method, attr_name = methods[content_type]
        file = FSInputFile(full_path)
        
        # Отправляем файл в тестовый чат для получения file_id
        result = await method(chat_id=-4723439111, **{content_type: file})
        
        # Получаем правильный атрибут с file_id
        media_object = getattr(result, attr_name)
        
        # Для фото получаем последнее (самое высокое разрешение)
        if content_type == 'photo':
            return media_object[-1].file_id
        return media_object.file_id

    except Exception as e:
        logger.error(f"Media upload error: {str(e)}")
        raise

def convert_keyboard_to_telegram_format(api_keyboard: dict) -> types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None:
    """Создание клавиатур с автоматическим заполнением payload для text-кнопок"""
    if not api_keyboard or not api_keyboard.get("buttons"):
        return None

    is_inline = api_keyboard.get("inline", False)
    
    try:
        if is_inline:
            keyboard = []
            for row in api_keyboard["buttons"]:
                keyboard_row = []
                for btn in row:
                    action = btn.get("action", {})
                    btn_type = action.get("type", "text")  # По умолчанию text
                    label = action.get("label", "")
                    
                    if not label:
                        continue  # Пропускаем кнопки без текста

                    # Обработка разных типов кнопок
                    if btn_type == "link":
                        keyboard_row.append(
                            InlineKeyboardButton(
                                text=label,
                                url=action.get("link", "")
                            )
                        )
                    elif btn_type in ["callback", "text"]:  # Объединяем callback и text
                        payload = action.get("payload", label)
                        # Обрезаем payload до 64 байт
                        payload = payload.encode()[:64].decode(errors='ignore')
                        keyboard_row.append(
                            InlineKeyboardButton(
                                text=label,
                                callback_data=payload
                            )
                        )
                    elif btn_type == "payment":
                        keyboard_row.append(
                            InlineKeyboardButton(
                                text=label,
                                pay=True
                            )
                        )
                    else:
                        continue  # Пропускаем неизвестные типы

                if keyboard_row:
                    keyboard.append(keyboard_row)
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

        else:
            # Обработка reply-клавиатуры
            builder = ReplyKeyboardBuilder()
            for row in api_keyboard["buttons"]:
                for btn in row:
                    action = btn.get("action", {})
                    btn_type = action.get("type", "text")
                    label = action.get("label", "")
                    
                    if btn_type == "location":
                        builder.add(KeyboardButton(
                            text=label,
                            request_location=True
                        ))
                    elif btn_type == "contact":
                        builder.add(KeyboardButton(
                            text=label,
                            request_contact=True
                        ))
                    elif btn_type == "text":
                        builder.add(KeyboardButton(text=label))
            
            markup = builder.as_markup()
            markup.resize_keyboard = api_keyboard.get("resize", True)
            markup.one_time_keyboard = api_keyboard.get("one_time", False)
            return markup

    except Exception as e:
        logger.error(f"Keyboard error: {str(e)}")
        return None

# Обработчики сообщений
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Обработка команды /start"""
    ref = message.text.split()[1] if len(message.text.split()) > 1 else None
    try:
        api_response = await send_to_api(
            user_id=message.from_user.id,
            content_type="command",
            command="start",
            ref=ref
        )
        await handle_api_response(message.from_user.id, api_response)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")

@dp.message(F.text)
async def handle_text(message: types.Message):
    """Обработка текстовых сообщений"""
    await process_message(
        message=message,
        content_type="text",
        message_text=message.text
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """Обработка фото"""
    await process_message(
        message=message,
        content_type="photo",
        file_id=message.photo[-1].file_id
    )

@dp.message(F.video)
async def handle_video(message: types.Message):
    """Обработка видео"""
    await process_message(
        message=message,
        content_type="video",
        file_id=message.video.file_id
    )

@dp.message(F.document)
async def handle_document(message: types.Message):
    """Обработка документов"""
    await process_message(
        message=message,
        content_type="document",
        file_id=message.document.file_id
    )

@dp.message(F.location)
async def handle_location(message: types.Message):
    """Обработка геолокации"""
    await process_message(
        message=message,
        content_type="location",
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    """Обработка голосовых сообщений"""
    await process_message(
        message=message,
        content_type="voice",
        file_id=message.voice.file_id
    )

@dp.message(F.video_note)
async def handle_video_note(message: types.Message):
    """Обработка видеосообщений"""
    await process_message(
        message=message,
        content_type="video_note",
        file_id=message.video_note.file_id
    )

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """Обработка контактов"""
    await process_message(
        message=message,
        content_type="contact",
        phone_number=message.contact.phone_number,
        first_name=message.contact.first_name,
        last_name=message.contact.last_name or ""
    )

async def process_message(message: types.Message, content_type: str, **kwargs):
    """Общая обработка сообщений"""
    user_id = message.from_user.id
    last_message_id = user_messages.get(user_id)
    
    try:
        api_response = await send_to_api(
            user_id=user_id,
            content_type=content_type,
            **kwargs
        )
        await handle_api_response(
            user_id=user_id,
            api_response=api_response,
            message_id=last_message_id,
            chat_id=user_id
        )
    except Exception as e:
        await message.answer(f"⚠️ Ошибка обработки: {str(e)}")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    """Обработка колбэков"""
    try:
        api_response = await send_to_api(
            user_id=callback.from_user.id,
            content_type="callback",
            callback_data=callback.data
        )
        await handle_api_response(
            user_id=callback.from_user.id,
            api_response=api_response,
            message_id=callback.message.message_id,
            chat_id=callback.from_user.id
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}", show_alert=True)

async def main():
    """Запуск бота"""
    print("📨 Telegram бот запущен", flush=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())