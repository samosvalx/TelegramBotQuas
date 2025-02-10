from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import logging
from datetime import datetime
import sqlite3
import os

# Настройки
BOT_TOKEN = '7648754388:AAHHCNW3hPftmixNpX_08i6mFonrJZ0mBGY'
CHANNELS = {
    '📢 Основной канал': '@quasarwxl',
    '📰 Новости': '@diipwebnews',
    '🔐 Базы | Логи': '@QuaSxw',
    '💬 Курилка | Обсуждения': '@offtop_kurilka'
}
ADMIN_CHAT_ID = 1078027776  # Замените на ваш ID

# Состояния для ConversationHandler
SENDING_MESSAGE = 0

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT)''')
    conn.commit()
    conn.close()

init_db()

def log_event(event: str, user_id: int = None, username: str = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_info = f"UserID: {user_id} | Username: @{username}" if user_id else "System"
    logger.info(f"[{timestamp}] {user_info} | Event: {event}")

def get_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def add_user(user_id: int, username: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# Клавиатуры
def subscription_keyboard():
    buttons = [
        [InlineKeyboardButton(text, url=f"https://t.me/{chat_id.lstrip('@')}")] 
        for text, chat_id in CHANNELS.items()
    ]
    buttons.append([InlineKeyboardButton("✅ Я подписался!", callback_data='check_sub')])
    return InlineKeyboardMarkup(buttons)

async def is_admin(user_id: int):
    return user_id == ADMIN_CHAT_ID

async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        for chat_id in CHANNELS.values():
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        return False

# Основные обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    log_event("Command /start received", user.id, user.username)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        "📢 Для доступа подпишись на наши каналы:",
        reply_markup=subscription_keyboard()
    )

async def handle_subscription_check(query, context: ContextTypes.DEFAULT_TYPE):
    user = query.from_user
    if await is_subscribed(user.id, context):
        await query.message.delete()
        await show_main_menu(context, user.id)
    else:
        await query.message.reply_text(
            "❌ Вы не подписаны на все каналы!",
            reply_markup=subscription_keyboard()
        )

async def show_main_menu(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    keyboard = [
        [InlineKeyboardButton("📚 Слив курсов", url='https://t.me/unhidden62bot')],
        [InlineKeyboardButton("🌑 Теневые форумы", url='https://t.me/shadowchatsforums')],
        [InlineKeyboardButton("💰 Заработок на верификациях", url='http://t.me/verifteam_bot?start=7314735680')],
        [InlineKeyboardButton("📱 Сдать WhatsApp", callback_data='rent_whatsapp')]
    ]
    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Доступ открыт! Выберите раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'check_sub':
        await handle_subscription_check(query, context)
    elif data == 'rent_whatsapp':
        await show_whatsapp_rent_menu(context, query.from_user.id)
    elif data == 'back_to_main':
        await show_main_menu(context, query.from_user.id)
    elif data.startswith('rent_'):
        await process_rent_selection(query, context)

async def show_whatsapp_rent_menu(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    keyboard = [
        [InlineKeyboardButton("⏳ 1 час - 4$", callback_data='rent_1')],
        [InlineKeyboardButton("⏳ 2 часа - 6$", callback_data='rent_2')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
    ]
    await context.bot.send_message(
        chat_id=user_id,
        text="📱 Выберите срок аренды WhatsApp:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_rent_selection(query, context):
    duration = query.data.split('_')[1]
    prices = {'1': '4$', '2': '6$'}
    
    rent_links = {
        '1': 'https://t.me/QuasWhatsAppOneBot',
        '2': 'https://t.me/WhatsAppQuasbot'
    }
    
    await query.message.edit_text(
        text=f"✅ Вы выбрали аренду на {duration} час(а) за {prices[duration]}\n\n"
             "⚠️ Для продолжения нажмите кнопку 'Сдать':\n\n"
             "📚 Ознакомьтесь с мануалом перед использованием:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Сдать", url=rent_links[duration])],
            [InlineKeyboardButton("📚 Мануал", url='https://telegra.ph/KAK-SDAT-WHATSAPP-02-10')],
            [InlineKeyboardButton("🔙 Назад", callback_data='rent_whatsapp')]
        ])
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды!")
        return
    
    await update.message.reply_text("✍️ Отправьте сообщение для рассылки:")
    return SENDING_MESSAGE

async def send_message_to_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    users = get_users()
    
    success = 0
    errors = 0
    for user_id in users:
        try:
            await message.copy(chat_id=user_id)
            success += 1
        except Exception as e:
            errors += 1
            logger.error(f"Ошибка отправки {user_id}: {str(e)}")
    
    await message.reply_text(f"✅ Рассылка завершена!\nУспешно: {success}\nОшибки: {errors}")
    return ConversationHandler.END

def main():
    log_event("Bot starting...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('br', broadcast)],
            states={
                SENDING_MESSAGE: [MessageHandler(filters.ALL, send_message_to_users)]
            },
            fallbacks=[]
        )
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(conv_handler)
        
        log_event("Bot started successfully")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")
        raise

if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    main()