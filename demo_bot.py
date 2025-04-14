from flask import Flask
from threading import Thread
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Flask сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 1874218277  # ID чата, куда приходят демки

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📤 Отправить демо", callback_data="send_demo")],
        [InlineKeyboardButton("📩 Обратная связь", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """🎵 Добро пожаловать в официальный бот музыкального лейбла unlimitedblades 🎵

Тут ты найдёшь всё, что нужно: отправка демо, обратная связь и многое другое.

📌 Используй команды ниже, чтобы быстро найти то, что тебе нужно.

🔹 /senddemo — отправка демо
🔹 /feedback — связаться с нами

Если есть звук — не держи в себе. Закидывай, мы слушаем. 🎧

____________________________________________________________________

🎵 Welcome to the official unlimitedblades music label bot 🎵

Here you'll find everything you need: demo submission, feedback, and much more.

📌 Use the commands below to quickly find what you need.

🔹 /senddemo — send demo
🔹 /feedback — contact us""",
        reply_markup=reply_markup
    )

async def send_demo_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Отправь мне свой трек в формате mp3 или wav файла! 🎵

Send me your track in mp3 or wav format! 🎵"""
    )

async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    file = message.audio or message.voice or message.document

    if not file:
        await message.reply_text("Пожалуйста, отправь аудио файл, голосовое или документ с треком.")
        return

    keyboard = [[
        InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user.id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"🎶 Новая демка от @{user.username or user.first_name} (ID: {user.id})"

    try:
        if message.audio:
            await context.bot.send_audio(chat_id=ADMIN_CHAT_ID, audio=file.file_id, caption=caption, reply_markup=reply_markup)
        elif message.voice:
            await context.bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=file.file_id, caption=caption, reply_markup=reply_markup)
        elif message.document:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=file.file_id, caption=caption, reply_markup=reply_markup)
        await message.reply_text("Спасибо! Твоя демка отправлена лейблу. 🔥")
    except Exception as e:
        await message.reply_text("Произошла ошибка при отправке демки. Попробуй ещё раз позже.")
        print(f"Ошибка при отправке демки: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "send_demo":
        await query.message.edit_text(
            """Отправь мне свой трек в формате mp3 или wav файла! 🎵

Send me your track in mp3 or wav format! 🎵""",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )
    elif data == "support":
        await query.message.edit_text(
            """📩 Для связи с поддержкой пишите: @unlimitedbladees

📩 For support, please contact: @unlimitedbladees""",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )
    elif data == "back":
        await start(query, context)
    elif "_" in data:
        action, user_id = data.split("_")
        if query.message.chat.id != ADMIN_CHAT_ID:
            return
        if action == "accept":
            await query.edit_message_caption(caption=f"{query.message.caption}

✅ Демка принята!", reply_markup=None)
            try:
                await context.bot.send_message(chat_id=user_id, text="🎉 Поздравляем! Ваша демка была принята!")
            except:
                print(f"Не удалось отправить сообщение пользователю {user_id}")
        elif action == "reject":
            await query.edit_message_caption(caption=f"{query.message.caption}

❌ Демка отклонена", reply_markup=None)
            try:
                await context.bot.send_message(chat_id=user_id, text="К сожалению, ваша демка была отклонена. Попробуйте отправить другой трек! 🎵")
            except:
                print(f"Не удалось отправить сообщение пользователю {user_id}")

if __name__ == "__main__":
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("senddemo", send_demo_instruction))
    application.add_handler(MessageHandler(filters.ATTACHMENT, handle_demo))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("feedback", lambda update, context: update.message.reply_text(
        """📩 Для связи с поддержкой пишите: @unlimitedbladees

📩 For support, please contact: @unlimitedbladees"""
    )))
    application.run_polling()