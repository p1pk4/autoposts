import telebot
from telebot import types
import openai
import os
import threading
import random
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Проверка, что токены загружены
if not all([TELEGRAM_TOKEN, OPENAI_API_KEY, CHANNEL_ID]):
    raise ValueError("Отсутствуют необходимые переменные окружения в .env файле")

GENERATION_INSTRUCTIONS = [
    # 1. Скрытая магия в обычных вещах
    "Возьми текст автора как отправную точку и создай короткую зарисовку, где обычные предметы скрывают тайных существ или магические силы. Покажи невидимую динамику за привычными вещами. Не цитируй автора — развивай его идею. До 350 символов.",

    # 2. Неоновый киберпанк
    "Переосмысли тему автора в духе неонового киберпанка: мегаполис, цифровые тени, импланты, корпорации и одиночество в толпе. Создай атмосферную сцену с запахом дождя на асфальте и мерцанием голограмм. До 350 символов.",

    # 3. Японский минимализм
    "Преврати тему автора в хайку-прозу: минимум слов, максимум ощущений. Пустота как смысл, тишина как звук, мгновение как вечность. Вдохновляйся дзен-буддизмом и японской эстетикой ваби-саби. До 350 символов.",

    # 4. Сюрреализм
    "Используй тему автора как трамплин в сюрреализм: логика сна, предметы меняют назначение, время течёт вспять, тени живут отдельно от тел. Создай образ, который удивляет и немного пугает своей красотой. До 350 символов.",

    # 5. Космос и бесконечность
    "Разверни тему автора до масштабов космоса: звёздная пыль, чёрные дыры, пульсары и молчание межзвёздного пространства. Покажи, как малое связано с бесконечным. До 350 символов.",

    # 6. Мифология и древние боги
    "Переложи тему автора на язык мифа: древние боги, герои, архетипы и вечные сюжеты. Говори как сказитель у костра — просто, но весомо. Пусть каждое слово несёт отзвук тысячелетий. До 350 символов.",

    # 7. Постапокалипсис
    "Помести тему автора в постапокалиптический мир: тишина после катастрофы, ржавые руины, первые цветы сквозь асфальт и люди, которые всё равно находят красоту. До 350 символов.",

    # 8. Детективный нуар
    "Пересмотри тему автора через линзу нуара: дождливый город, одинокий детектив, секреты за каждой дверью. Короткий, плотный текст с атмосферой опасности и обречённой романтики. До 350 символов.",

    # 9. Волшебная сказка
    "Преврати тему автора в фрагмент волшебной сказки: говорящие животные, заколдованные предметы, лес с характером, загадочный незнакомец. Тон — тёплый и немного таинственный. До 350 символов.",

    # 10. Философская медитация
    "Возьми тему автора и разверни её в короткое философское эссе: что это значит для человека, как это связано с бытием, памятью или свободой? Без пафоса — честно и точно. До 350 символов.",

    # 11. Импрессионизм
    "Опиши тему автора как импрессионистскую картину: размытые контуры, игра света и тени, запахи смешиваются с цветами. Не рассказывай — рисуй словами. До 350 символов.",

    # 12. Ретрофутуризм (стиль 60-х)
    "Переосмысли тему автора в духе ретрофутуризма 1960-х: атомный оптимизм, хромированные ракеты, мечты о светлом завтра и наивная вера в прогресс. До 350 символов.",

    # 13. Синестезия
    "Опиши тему автора через синестезию: какой у неё вкус, запах, цвет и текстура? Смешай чувства так, чтобы читатель ощутил описываемое всем телом. До 350 символов.",

    # 14. Морская стихия
    "Свяжи тему автора с океаном: глубины, течения, штормы, существа из бездны, тишина под водой и безграничный горизонт. Текст должен ритмично колыхаться, как волна. До 350 символов.",

    # 15. Городская поэзия
    "Переложи тему автора в жанр городской поэзии: метро в час пик, кофе в одноразовом стакане, незнакомцы с целыми жизнями за глазами. Жёстко, нежно, живо. До 350 символов.",

    # 16. Мистика и потусторонний мир
    "Преврати тему автора в мистическую зарисовку: тонкая грань между мирами, шёпот из темноты, предметы с памятью и присутствие тех, кого уже нет. Не пугай — завораживай. До 350 символов.",

    # 17. Романтика и чувственность
    "Разверни тему автора в романтическую сцену: трепет, предвкушение, взгляды которые говорят больше слов, и мгновения которые хочется остановить. Чувственно, но не пошло. До 350 символов.",

    # 18. Абсурдизм
    "Возьми тему автора и доведи её до абсурда в духе Кафки или Хармса: нелепая логика, серьёзный тон при смешных обстоятельствах, мир чуть левее реальности. До 350 символов.",

    # 19. Природа и дикий мир
    "Переосмысли тему автора через дикую природу: лес как живой организм, миграции птиц, запах земли после дождя, язык животных которого мы разучились слышать. До 350 символов.",

    # 20. Временны́е петли и ностальгия
    "Свяжи тему автора с памятью и временем: запах который телепортирует в детство, города которых больше нет, люди которые изменились и всё равно остались собой. До 350 символов.",
]

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# Глобальный словарь для хранения данных пользователя (только один ключ - chat_id)
user_data = {}


def generate_text(input_text):
    """Генерирует текст через OpenAI с обработкой ошибок"""
    try:
        instruction = random.choice(GENERATION_INSTRUCTIONS)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Заменено с gpt-4-turbo
            messages=[
                {"role": "system", "content": instruction},
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