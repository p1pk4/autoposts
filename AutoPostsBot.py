import telebot
from telebot import types
import openai
import os
import threading
from dotenv import load_dotenv

# Загрузка и установка переменных окружения
# load_dotenv('D:/_iiLight/autoTGpostsBot/autoTGpostsBot.env')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

GENERATION_INSTRUCTIONS = "Создайте текст, который основан на личных размышлениях и эмоциональных переживаниях " \
                          "автора. Используйте информацию из подписи, чтобы погрузиться в глубину мыслей о прошлом, " \
                          "ностальгии и человеческих связях. При этом текст должен быть простым, но проникновенным, " \
                          "добавляя неожиданные и трогательные детали, которые помогут читателю увидеть мир глазами " \
                          "автора. Текст должен вдохновлять и наполнять чувством тепла, делая каждый момент " \
                          "особенным. Используя следующую информацию как основную тему: {input_text}."



# Инициализация бота Telegram и OpenAI

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY


# Функция генерации текста с помощью OpenAI
def generate_text(input_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": GENERATION_INSTRUCTIONS},
                      {"role": "user", "content": input_text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating text from OpenAI: {e}")
        return "Произошла ошибка при генерации текста."


# Функция создания клавиатуры для взаимодействия с пользователем
def get_keyboard():
    markup = types.InlineKeyboardMarkup()
    send_btn = types.InlineKeyboardButton("🚀", callback_data='post')
    regenerate_btn = types.InlineKeyboardButton("🧠", callback_data='regenerate')
    cancel_btn = types.InlineKeyboardButton("💀", callback_data='cancel')
    help_btn = types.InlineKeyboardButton("Help ❓", callback_data='help')
    markup.row(send_btn, regenerate_btn)
    markup.row(cancel_btn, help_btn)
    return markup


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Теперь при старте (или после отправки поста) сбрасываем данные пользователя
    chat_id = message.chat.id
    user_data[chat_id] = {'photos': [], 'text': ''}
    bot.reply_to(message, 'Привет! 👋 Отправьте текст или фото натяжных потолков, и я создам для вас пост. 🛠️')


# Глобальный словарь для хранения данных пользователя
user_data = {}


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Сбрасываем данные пользователя при получении нового текста
    user_data[chat_id] = {'photos': [], 'text': '', 'timer': None}  # Добавить эту строку

    if not text:
        bot.send_message(chat_id, "Кажется, ваше сообщение пустое. 🤔 Напишите что-нибудь, чтобы продолжить!")
        return
    # Проверяем, есть ли уже данные для этого chat_id, инициализируем если нет
    if chat_id not in user_data:
        user_data[chat_id] = {'photos': [], 'text': '', 'timer': None}
    user_data[chat_id]['text'] = text
    generated_text = generate_text(text)
    user_data[chat_id]['generated_text'] = generated_text
    bot.send_message(chat_id, generated_text, reply_markup=get_keyboard())


# Функция для обработки пака фотографий
def process_photo_pack(chat_id):
    # Обработка пака фотографий, генерация текста и отправка клавиатуры
    generated_text = generate_text(user_data[chat_id]['text'])
    user_data[chat_id]['generated_text'] = generated_text
    bot.send_message(chat_id, generated_text, reply_markup=get_keyboard())

    # Сбрасываем текст после генерации
    user_data[chat_id]['text'] = ''

# Обработчик получения фотографий
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id

    # Сбрасываем данные пользователя при получении нового фото
    user_data[chat_id] = {'photos': [], 'text': '', 'timer': None}

    ## Проверяем, есть ли уже данные для этого chat_id, инициализируем если нет
    #if chat_id not in user_data:
     #   user_data[chat_id] = {'photos': [], 'text': '', 'timer': None}

    photo_id = message.photo[-1].file_id
    user_data[chat_id]['photos'].append(photo_id)
    # Если пользователь прислал подпись к фото, добавляем ее в текст
    if message.caption:
        user_data[chat_id]['text'] += ' ' + message.caption
    # Отменяем существующий таймер, если он есть
    if user_data[chat_id].get('timer'):
        user_data[chat_id]['timer'].cancel()
    # Устанавливаем новый таймер
    user_data[chat_id]['timer'] = threading.Timer(3.0, process_photo_pack, [chat_id])
    user_data[chat_id]['timer'].start()


# Эта функция вызывается после добавления фотографии или текста
def generate_and_send_text(chat_id):
    text_to_generate = user_data[chat_id]['text'] if user_data[chat_id]['text'] else GENERATION_INSTRUCTIONS
    generated_text = generate_text(text_to_generate)
    user_data[chat_id]['generated_text'] = generated_text
    bot.send_message(chat_id, generated_text, reply_markup=get_keyboard())
    # Отправляем меню только один раз
    if 'sent_keyboard' not in user_data[chat_id]:
        bot.send_message(chat_id, "Выберите действие:", reply_markup=get_keyboard())
        user_data[chat_id]['sent_keyboard'] = True


# Отмена текущего действия и сброс состояния
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def handle_cancel(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    # Сбрасываем данные пользователя
    user_data[user_id] = {'photos': [], 'text': '', 'timer': None}
    bot.answer_callback_query(call.id, "Вы отменили создание поста. Начнем заново? 🔄")
    bot.send_message(chat_id, "Вы отменили создание поста. Начнем заново? 🔄")


# Отправка поста в канал
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if call.data == 'post':
        if 'photos' in user_data[user_id] and user_data[user_id]['photos']:
            # Создаем медиа-группу из фотографий и добавляем к первой фотографии сгенерированный текст
            media_group = [types.InputMediaPhoto(photo) for photo in user_data[user_id]['photos']]
            media_group[0].caption = user_data[user_id]['generated_text']
            # Отправляем медиа-группу в канал
            bot.send_media_group(CHANNEL_ID, media_group)
            bot.send_message(chat_id, "Ваш пост успешно опубликован в канале! 🚀")
            # Сброс данных пользователя после отправки поста
            user_data[user_id] = {'photos': [], 'text': ''}

        else:
            bot.send_message(chat_id, "Чтобы опубликовать пост, мне нужна хотя бы одна фотография. 📷")
        user_data[user_id] = {'photos': [], 'text': '', 'timer': None}
    elif call.data == 'regenerate':
        # Удаляем проверку на то, что новый текст отличается от старого
        # и всегда генерируем новый текст
        new_text = generate_text(user_data[user_id]['text'])
        user_data[user_id]['generated_text'] = new_text
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=new_text,
                              reply_markup=get_keyboard())
        bot.answer_callback_query(call.id)
    elif call.data == 'help':
        help_text = """
        🤖 *Как использовать бота:*

*Просто отправьте фото:* Не нужно писать текст! Просто отправьте одну или несколько фотографий, и я сгенерирую к ним уникальное описание. Это самый быстрый способ создать пост.

*Отправка текста:* Напишите любой текст, и я сгенерирую для вас уникальное описание. Это может быть краткое описание вашей фотографии или идея для поста.

*Добавление подписи к фото:* Если отправляете фото, можете добавить к нему подпись. Я учту её при создании текста.

*Создание поста:* Вы можете комбинировать текст и фотографии, отправляя их в любом порядке. Я создам пост, основываясь на всей отправленной информации.

*Работа с кнопками:*
🚀 *Отправить:* Публикует пост с вашим текстом и/или фотографиями в канале.
🧠 *Сгенерировать заново:* Создает новый текст на основе вашего последнего сообщения или фотографии.
💀 *Отмена:* Отменяет текущий пост и сбрасывает все введенные данные.


👉 Начните с отправки текста или фотографии, и я помогу вам с созданием поста!

        """

        bot.send_message(chat_id, help_text, parse_mode='Markdown')
    bot.answer_callback_query(call.id)


# Запуск бота
bot.polling(none_stop=True)
