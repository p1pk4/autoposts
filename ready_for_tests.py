import telebot
from telebot import types
import openai
import os
import threading
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Проверка, что токены загружены
if not all([TELEGRAM_TOKEN, OPENAI_API_KEY, CHANNEL_ID]):
    raise ValueError("Отсутствуют необходимые переменные окружения в .env файле")

GENERATION_INSTRUCTIONS = "Используйте текст автора как основу для создания уникального воображаемого мира, где любые "\
                          "объекты скрывают тайные существа, силы или магические " \
                          "процессы, которые управляют их существованием или поведением. Расширяйте идею, добавляя " \
                          "неожиданные детали — возможно, существа, живущие внутри граффити, или энергии, которые " \
                          "приводят в движение статичные предметы. Каждое описание должно показывать скрытую " \
                          "динамику или магию в привычных вещах. " \
                          "Стремитесь к оригинальности, чередуйте атмосферу — от лёгкого, воздушного повествования до "\
                          "насыщенных образов, вызывающих удивление и вдохновение. Не повторяйте текст автора " \
                          "дословно, а дополняйте его, развивая и расширяя мир. " \
                          "Каждый текст должен быть коротким, увлекательным и наполненным элементами фантазии, " \
                          "сохраняя художественную плавность. Ограничение: не более 350 символов. " \
                          "Используя следующую информацию как основную тему: {input_text}."

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# Глобальный словарь для хранения данных пользователя (только один ключ - chat_id)
user_data = {}


def generate_text(input_text):
    """Генерирует текст через OpenAI с обработкой ошибок"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Заменено с gpt-4-turbo
            messages=[
                {"role": "system", "content": GENERATION_INSTRUCTIONS},
                {"role": "user", "content": input_text}
            ],
            timeout=15  # Timeout 15 сек
        )
        return response.choices[0].message.content.strip()
    except openai.error.Timeout:
        return "⏱️ Время ожидания истекло. Попробуйте ещё раз."
    except openai.error.APIError as e:
        print(f"OpenAI API Error: {e}")
        return "❌ Ошибка API OpenAI. Попробуйте позже."
    except Exception as e:
        print(f"Error generating text: {e}")
        return "❌ Произошла ошибка при генерации текста."


def get_keyboard():
    """Создаёт клавиатуру с кнопками"""
    markup = types.InlineKeyboardMarkup()
    send_btn = types.InlineKeyboardButton("🚀 Отправить", callback_data='post')
    regenerate_btn = types.InlineKeyboardButton("🧠 Заново", callback_data='regenerate')
    cancel_btn = types.InlineKeyboardButton("💀 Отмена", callback_data='cancel')
    help_btn = types.InlineKeyboardButton("❓ Помощь", callback_data='help')
    markup.row(send_btn, regenerate_btn)
    markup.row(cancel_btn, help_btn)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    chat_id = message.chat.id
    user_data[chat_id] = {'photos': [], 'text': '', 'generated_text': '', 'timer': None}
    bot.reply_to(message, 
                 'Привет! 👋\n\n'
                 'Отправьте текст или фото, и я создам для вас уникальный пост.\n\n'
                 'Команды:\n'
                 '/help - справка\n'
                 '/start - начать заново')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    text = message.text.strip()

    if not text:
        bot.send_message(chat_id, "Сообщение пустое. 🤔 Напишите что-нибудь!")
        return

    # Инициализируем данные, если это новый пользователь
    if chat_id not in user_data:
        user_data[chat_id] = {'photos': [], 'text': '', 'generated_text': '', 'timer': None}

    # Отменяем старый таймер, если существует
    if user_data[chat_id].get('timer'):
        user_data[chat_id]['timer'].cancel()

    user_data[chat_id]['text'] = text
    
    # Показываем, что генерируем
    processing_msg = bot.send_message(chat_id, "⏳ Генерирую текст...")
    
    generated_text = generate_text(text)
    user_data[chat_id]['generated_text'] = generated_text

    # Заменяем сообщение "генерирую" на результат
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_msg.message_id,
            text=generated_text,
            reply_markup=get_keyboard()
        )
    except:
        bot.send_message(chat_id, generated_text, reply_markup=get_keyboard())


def process_photo_pack(chat_id):
    """Обрабатывает пак фотографий после задержки"""
    if chat_id not in user_data:
        return
    
    text_to_generate = user_data[chat_id]['text'] if user_data[chat_id]['text'] else "Фото без описания"
    
    processing_msg = bot.send_message(chat_id, "⏳ Генерирую текст для фото...")
    generated_text = generate_text(text_to_generate)
    user_data[chat_id]['generated_text'] = generated_text

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_msg.message_id,
            text=generated_text,
            reply_markup=get_keyboard()
        )
    except:
        bot.send_message(chat_id, generated_text, reply_markup=get_keyboard())


@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """Обработчик получения фотографий"""
    chat_id = message.chat.id

    # Инициализируем данные, если это новый пользователь
    if chat_id not in user_data:
        user_data[chat_id] = {'photos': [], 'text': '', 'generated_text': '', 'timer': None}

    photo_id = message.photo[-1].file_id
    user_data[chat_id]['photos'].append(photo_id)

    # Добавляем подпись к фото
    if message.caption:
        user_data[chat_id]['text'] += ' ' + message.caption

    # Отменяем старый таймер
    if user_data[chat_id].get('timer'):
        user_data[chat_id]['timer'].cancel()

    # Устанавливаем новый таймер (ждём 3 сек, может быть ещё фото)
    user_data[chat_id]['timer'] = threading.Timer(3.0, process_photo_pack, [chat_id])
    user_data[chat_id]['timer'].start()
    
    bot.send_message(chat_id, f"📸 Получил фото ({len(user_data[chat_id]['photos'])} шт.). Жду ещё 3 сек...")


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def handle_cancel(call):
    """Отмена текущей операции"""
    chat_id = call.message.chat.id
    
    if chat_id in user_data and user_data[chat_id].get('timer'):
        user_data[chat_id]['timer'].cancel()
    
    user_data[chat_id] = {'photos': [], 'text': '', 'generated_text': '', 'timer': None}
    bot.answer_callback_query(call.id, "Отменено 💀")
    bot.send_message(chat_id, "Начнем заново? Отправьте текст или фото.")


@bot.callback_query_handler(func=lambda call: call.data == 'post')
def handle_post(call):
    """Публикует пост в канал"""
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "❌ Ошибка: данные потеряны")
        return

    try:
        if user_data[chat_id]['photos']:
            # Создаем медиа-группу из фотографий
            media_group = [types.InputMediaPhoto(photo) for photo in user_data[chat_id]['photos']]
            media_group[0].caption = user_data[chat_id]['generated_text']
            
            # Отправляем в канал
            bot.send_media_group(CHANNEL_ID, media_group)
            bot.send_message(chat_id, "✅ Пост опубликован в канале! 🚀")
        else:
            # Публикуем просто текст
            bot.send_message(CHANNEL_ID, user_data[chat_id]['generated_text'])
            bot.send_message(chat_id, "✅ Пост опубликован в канале! 🚀")
        
        # Сбрасываем данные
        user_data[chat_id] = {'photos': [], 'text': '', 'generated_text': '', 'timer': None}
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error posting: {e}")
        bot.send_message(chat_id, f"❌ Ошибка при публикации: {str(e)}")
        bot.answer_callback_query(call.id, "❌ Ошибка")


@bot.callback_query_handler(func=lambda call: call.data == 'regenerate')
def handle_regenerate(call):
    """Генерирует новый текст"""
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "❌ Ошибка: данные потеряны")
        return

    new_text = generate_text(user_data[chat_id]['text'])
    user_data[chat_id]['generated_text'] = new_text

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=new_text,
            reply_markup=get_keyboard()
        )
        bot.answer_callback_query(call.id, "🧠 Переписал")
    except:
        bot.send_message(chat_id, new_text, reply_markup=get_keyboard())
        bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'help')
def handle_help(call):
    """Справка"""
    chat_id = call.message.chat.id
    help_text = """🤖 *Как пользоваться ботом:*

*Вариант 1: Только фото*
Просто отправьте одну или несколько фотографий, и я сгенерирую к ним уникальное описание.

*Вариант 2: Только текст*
Напишите текст, и я развью его в уникальное описание.

*Вариант 3: Фото + подпись*
Отправьте фото с подписью (caption), я учту обе части.

*Кнопки:*
🚀 *Отправить* — публикует пост в канал
🧠 *Заново* — генерирует новый текст
💀 *Отмена* — отменяет и сбрасывает данные
❓ *Помощь* — эта справка

*Важное:*
- Пост публикуется в канал только при нажатии 🚀
- Если отправляете несколько фото, подождите 3 сек между ними
- Каждое сообщение = новый пост

Начните с отправки фото или текста! 📸📝
    """
    bot.send_message(chat_id, help_text, parse_mode='Markdown')
    bot.answer_callback_query(call.id)


# Запуск бота
if __name__ == '__main__':
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)