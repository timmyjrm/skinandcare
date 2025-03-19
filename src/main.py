import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()
# Get admin chat ID
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
RECIPIENT_IDS = [id.strip() for id in os.getenv("RECIPIENT_IDS", "").split(",") if id.strip()]

# Global variable to track current recipient index
current_recipient_index = 0

def get_next_recipient():
    """Get next recipient ID in rotation."""
    global current_recipient_index
    if not RECIPIENT_IDS:
        return None
    
    recipient_id = RECIPIENT_IDS[current_recipient_index]
    current_recipient_index = (current_recipient_index + 1) % len(RECIPIENT_IDS)
    return recipient_id

# States for conversation
(
    WAITING_FOR_NAME,
    WAITING_FOR_AGE,
    WAITING_FOR_CITY,
    WAITING_FOR_MEDIA,
    QUESTION_1,
    QUESTION_2,
    QUESTION_3,
    QUESTION_4,
    QUESTION_5,
    CONTACT_SHARING,
) = range(10)

# Questions and their possible answers
QUESTIONS = {
    QUESTION_1: {
        "text": "1️⃣ Как бы вы описали вашу кожу в течение дня?",
        "options": [["Жирная", "Сухая"], ["Комбинированная", "Нормальная"]]
    },
    QUESTION_2: {
        "text": "2️⃣ Беспокоят ли вас воспаления на коже?",
        "options": [["Часто", "Иногда"], ["Редко", "Никогда"]]
    },
    QUESTION_3: {
        "text": "3️⃣ Какие проблемы с кожей вас беспокоят больше всего?",
        "options": [["Тусклость", "Поры"], ["Неровный тон", "Шелушение"]]
    },
    QUESTION_4: {
        "text": "4️⃣ Как часто вы ухаживаете за кожей?",
        "options": [["Ежедневно", "2-3 раза в неделю"], ["Редко", "Никогда"]]
    },
    QUESTION_5: {
        "text": "5️⃣ Какой бюджет вы готовы выделить на уход за кожей в месяц?",
        "options": [["До 3000₽", "3000-7000₽"], ["7000-15000₽", "Более 15000₽"]]
    }
}

# Store user answers
user_answers = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and ask for name."""
    # Clear all user data when starting new conversation
    context.user_data.clear()
    
    welcome_message = (
        "👋 Здравствуйте! Я ваш персональный консультант по уходу за кожей.\n\n"
        "Я помогу определить тип вашей кожи и подберу индивидуальные рекомендации "
        "на основе фото или видео, которые вы отправите.\n\n"
        "Давайте познакомимся! Как вас зовут? 😊"
    )
    await update.message.reply_text(welcome_message)
    return WAITING_FOR_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name and ask for age."""
    name = update.message.text
    context.user_data['name'] = name
    
    await update.message.reply_text(
        f"Приятно познакомиться, {name}! ✨\n"
        "Сколько вам лет?"
    )
    return WAITING_FOR_AGE

async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's age and ask for city."""
    age = update.message.text
    
    # Store age
    context.user_data['age'] = age
    
    # Ask for city
    await update.message.reply_text(
        "В каком городе вы находитесь? 🏙️\n"
        "Пожалуйста, напишите название города."
    )
    return WAITING_FOR_CITY

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's city and ask for photo."""
    city = update.message.text
    name = context.user_data.get('name', 'Уважаемый клиент')
    
    # Store city
    context.user_data['city'] = city
    
    # Ask for photo
    await update.message.reply_text(
        f"{name}, теперь, пожалуйста, отправьте фото или видео вашей кожи 📸\n"
        "Это поможет нам лучше оценить её состояние."
    )
    return WAITING_FOR_MEDIA

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received photo or video and proceed to questions."""
    name = context.user_data.get('name', 'Уважаемый клиент')
    age = context.user_data.get('age', 'Не указан')
    city = context.user_data.get('city', 'Не указан')
    
    # Store the file_id of the media
    if update.message.photo:
        context.user_data['media_type'] = 'photo'
        context.user_data['media_id'] = update.message.photo[-1].file_id
    elif update.message.video:
        context.user_data['media_type'] = 'video'
        context.user_data['media_id'] = update.message.video.file_id
    
    await update.message.reply_text(
        f"Спасибо, {name}! 🌟\n\n"
        "Теперь давайте ответим на несколько вопросов, чтобы я мог(ла) "
        "точнее определить потребности вашей кожи."
    )
    
    # Start with the first question
    question = QUESTIONS[QUESTION_1]
    reply_markup = ReplyKeyboardMarkup(
        question["options"], one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(question["text"], reply_markup=reply_markup)
    return QUESTION_1

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's answer and proceed to the next question."""
    user_id = update.effective_user.id
    answer = update.message.text
    current_question = context.user_data.get('current_question', QUESTION_1)
    
    # Store the answer
    if 'answers' not in context.user_data:
        context.user_data['answers'] = {}
    context.user_data['answers'][current_question] = answer
    
    # Determine next question
    next_question = None
    if current_question == QUESTION_1:
        next_question = QUESTION_2
    elif current_question == QUESTION_2:
        next_question = QUESTION_3
    elif current_question == QUESTION_3:
        next_question = QUESTION_4
    elif current_question == QUESTION_4:
        next_question = QUESTION_5
    
    if next_question:
        # Store current question for next iteration
        context.user_data['current_question'] = next_question
        
        # Send next question
        question = QUESTIONS[next_question]
        reply_markup = ReplyKeyboardMarkup(
            question["options"], one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(question["text"], reply_markup=reply_markup)
        return next_question
    else:
        # All questions answered, proceed to recommendations
        return await handle_final_question(update, context)

async def handle_final_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle final question and provide recommendations."""
    user_id = update.effective_user.id
    answers = context.user_data.get('answers', {})
    name = context.user_data.get('name', 'Уважаемый клиент')
    age = context.user_data.get('age', 'Не указан')
    city = context.user_data.get('city', 'Не указан')
    
    skin_type = answers.get(QUESTION_1, "")
    acne = answers.get(QUESTION_2, "")
    skin_concern = answers.get(QUESTION_3, "")
    care_frequency = answers.get(QUESTION_4, "")
    budget = answers.get(QUESTION_5, "")
    
    recommendation = f"🎉 {name}, спасибо за ваши ответы! Вот ваши персональные рекомендации:\n\n"
    
    # Базовые рекомендации по типу кожи
    if skin_type == "Жирная":
        recommendation += (
            "📌 Для жирной кожи рекомендуем:\n"
            "• Использовать легкие гелевые текстуры\n"
            "• Средства с салициловой кислотой\n"
            "• Матирующие тоники без спирта\n\n"
        )
    elif skin_type == "Сухая":
        recommendation += (
            "📌 Для сухой кожи рекомендуем:\n"
            "• Кремы с плотной текстурой\n"
            "• Средства с гиалуроновой кислотой\n"
            "• Масла для дополнительного питания\n\n"
        )
    elif skin_type == "Комбинированная":
        recommendation += (
            "📌 Для комбинированной кожи рекомендуем:\n"
            "• Разные средства для разных зон лица\n"
            "• Легкие увлажняющие текстуры\n"
            "• Балансирующие тоники\n\n"
        )
    elif skin_type == "Нормальная":
        recommendation += (
            "📌 Для нормальной кожи рекомендуем:\n"
            "• Поддерживающий базовый уход\n"
            "• Увлажняющие средства\n"
            "• Мягкое очищение\n\n"
        )
    
    # Рекомендации по воспалениям
    if acne == "Часто" or acne == "Иногда":
        recommendation += (
            "🔍 Для борьбы с воспалениями:\n"
            "• Точечные средства с цинком\n"
            "• Противовоспалительные сыворотки\n"
            "• Очищающие маски 1-2 раза в неделю\n\n"
        )
    
    # Рекомендации по конкретным проблемам
    if skin_concern == "Тусклость":
        recommendation += (
            "✨ Для сияния кожи:\n"
            "• Средства с витамином С\n"
            "• Мягкие пилинги\n"
            "• Увлажняющие маски\n\n"
        )
    elif skin_concern == "Поры":
        recommendation += (
            "🔍 Для сужения пор:\n"
            "• Средства с ниацинамидом\n"
            "• Глиняные маски\n"
            "• Тоники с BHA-кислотами\n\n"
        )
    elif skin_concern == "Неровный тон":
        recommendation += (
            "🎨 Для выравнивания тона:\n"
            "• Средства с арбутином\n"
            "• Осветляющие сыворотки\n"
            "• АНА-кислоты\n\n"
        )
    elif skin_concern == "Шелушение":
        recommendation += (
            "🍯 При шелушении кожи:\n"
            "• Средства с керамидами\n"
            "• Питательные маски\n"
            "• Мягкие скрабы\n\n"
        )
    
    # Рекомендации по частоте ухода
    if care_frequency in ["Редко", "Никогда"]:
        recommendation += (
            "⏰ Важное напоминание:\n"
            "Регулярный уход - ключ к здоровой коже! Начните с простого:\n"
            "• Утро: умывание → увлажнение → защита\n"
            "• Вечер: очищение → уход → увлажнение\n\n"
        )
    elif care_frequency == "2-3 раза в неделю":
        recommendation += (
            "📅 Для улучшения результатов:\n"
            "Постарайтесь ухаживать за кожей ежедневно:\n"
            "• Утренний и вечерний уход\n"
            "• Дополнительные маски 1-2 раза в неделю\n\n"
        )
    
    # Добавляем предложение связаться со специалистом
    contact_message = (
        "👩‍⚕️ Хотите получить более детальную консультацию?\n"
        "Этот бот может отправит ваш контакт специалистам, которые помогут подобрать индивидуальный уход "
        "и профессиональные процедуры для вашей кожи.\n\n"
        "Бот не связан ни с одной конкретной клиникой, а подстраивается под ваши потребности и возможности.\n\n "
        "Нажмите кнопку ниже, чтобы поделиться контактом:"
    )
    
    await update.message.reply_text(recommendation)
    
    # Create contact sharing button
    contact_button = KeyboardButton("📱 Поделиться контактом", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True)
    
    await update.message.reply_text(contact_message, reply_markup=reply_markup)
    
    # Clear user answers but keep the name and age
    user_answers.pop(user_id, None)
    return CONTACT_SHARING

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared contact information and send application to admin."""
    contact = update.message.contact
    name = context.user_data.get('name', 'клиент')
    age = context.user_data.get('age', 'Не указан')
    city = context.user_data.get('city', 'Не указан')
    media_type = context.user_data.get('media_type')
    media_id = context.user_data.get('media_id')
    
    # Prepare application text
    application = (
        "🔔 НОВАЯ ЗАЯВКА!\n\n"
        f"👤 Имя: {name}\n"
        f"📅 Возраст: {age}\n"
        f"🏙️ Город: {city}\n"
        f"📱 Телефон: {contact.phone_number}\n\n"
        "📋 Ответы на вопросы:\n"
    )
    
    # Add answers to the application
    answers = context.user_data.get('answers', {})
    for q_num, q_data in QUESTIONS.items():
        answer = answers.get(q_num, "Нет ответа")
        question_text = q_data["text"].split('️⃣ ')[1] if '️⃣ ' in q_data["text"] else q_data["text"]
        application += f"{question_text}\n➡️ {answer}\n\n"
    
    try:
        # Get next recipient in rotation
        recipient_id = get_next_recipient()
        if not recipient_id:
            raise Exception("Нет доступных получателей заявок")
        
        print(f"Attempting to send application to recipient: {recipient_id}")
        
        # First send media to the recipient
        if media_type == 'photo':
            await context.bot.send_photo(
                chat_id=recipient_id,
                photo=media_id,
                caption="📸 Фото клиента"
            )
        elif media_type == 'video':
            await context.bot.send_video(
                chat_id=recipient_id,
                video=media_id,
                caption="🎥 Видео клиента"
            )
        
        # Then send application text to the recipient
        await context.bot.send_message(
            chat_id=recipient_id,
            text=application,
            parse_mode='HTML'
        )
        
        print(f"Successfully sent application to recipient: {recipient_id}")
        
        # Send notification to admin
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"✅ Новая заявка от {name} отправлена получателю {recipient_id}"
        )
    except Exception as e:
        error_message = f"Error sending application: {str(e)}"
        print(error_message)
        print(f"Current recipient IDs: {RECIPIENT_IDS}")
        print(f"Current recipient index: {current_recipient_index}")
        
        # Try to notify admin about the error
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"❌ Ошибка при отправке заявки от {name}:\n{error_message}\n\n"
                     f"Проверьте, что бот добавлен в чат {recipient_id} и имеет права администратора."
            )
        except Exception as admin_error:
            print(f"Failed to notify admin: {str(admin_error)}")
    
    # Clear state but keep name for the final message
    temp_name = context.user_data.get('name')
    context.user_data.clear()
    context.user_data['name'] = temp_name
    
    # Remove keyboard and send final message
    reply_markup = ReplyKeyboardRemove()
    
    await update.message.reply_text(
        f"Спасибо, {name}! 🙏\n\n"
        "Ваша заявка отправлена. Специалисты свяжутся с вами в ближайшее время "
        "для предоставления персональной консультации.\n\n"
        "Если у вас появятся новые вопросы, просто напишите /start",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    # Clear all user data when canceling
    context.user_data.clear()
    
    # Remove keyboard
    reply_markup = ReplyKeyboardRemove()
    
    await update.message.reply_text(
        "Диалог прерван. Чтобы начать заново, напишите /start",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

def main():
    """Main function to run the bot."""
    # Get bot token from .env file
    try:
        with open('.env', 'r') as f:
            line = f.readline().strip()
            bot_token = line.split('=')[1].strip('"')  # Remove quotes if present
        print(f"Bot token loaded successfully")
    except Exception as e:
        print(f"Error loading token: {e}")
        return
    
    if not bot_token:
        print("Error: BOT_TOKEN not found")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            WAITING_FOR_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)
            ],
            WAITING_FOR_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)
            ],
            WAITING_FOR_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO, handle_media)
            ],
            QUESTION_1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)
            ],
            QUESTION_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)
            ],
            QUESTION_3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)
            ],
            QUESTION_4: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)
            ],
            QUESTION_5: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)
            ],
            CONTACT_SHARING: [
                MessageHandler(filters.CONTACT, handle_contact)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Start the bot
    print("CosmetBot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

    
    