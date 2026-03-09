from telegram import Update, BotCommand, BotCommandScopeChat
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

from gpt import ChatGptService
from states_test import get_profile_conversation_handler
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt)
from credentials import config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'movie': 'Рекомендації щодо фільмів та книг'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt("random")
    message = await update.message.reply_text("Зачекайте декілька секунд...")

    chat_gpt = ChatGptService(config.OPENAI_TOKEN)

    chat_gpt.set_prompt(prompt)
    response_text = await chat_gpt.send_message_list()
    await message.edit_text(response_text)

async def gpt(update, context): # опрацювання команди /gpt
    prompt = load_prompt("gpt")
    await send_image(update, context, "gpt")
    message = load_message("gpt")
    await send_text(update, context, message)

async def gpt_dialog(update, context):  # опрацювання команди /gpt
    text = update.message.text
    prompt = load_prompt("gpt")
    chat_gpt = ChatGptService(config.OPENAI_TOKEN)
    answer = await chat_gpt.send_question(prompt, text)
    await send_text(update, context, answer)


def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).concurrent_updates(True).build()

    # Зареєструвати обробник команди можна так:
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('random', random))
    app.add_handler(CommandHandler('gpt', gpt))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_dialog))
    app.add_handler(get_profile_conversation_handler())

# Зареєструвати обробник колбеку можна так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()