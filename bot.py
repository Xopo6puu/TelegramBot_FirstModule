from telegram import Update, BotCommand, BotCommandScopeChat, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
import asyncio
import logging

from gpt import ChatGptService
from states_test import get_profile_conversation_handler
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, load_instructions)
from credentials import config
from keyboards.gpt_keyboard import gpt_keyboard


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

    })

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt("random")
    message = await update.message.reply_text("Зачекайте декілька секунд...")

    chat_gpt = ChatGptService(config.OPENAI_TOKEN)

    chat_gpt.set_prompt(prompt)
    response_text = await chat_gpt.send_message_list()
    await message.edit_text(response_text)

GPT_DIALOG = 1

async def gpt(update, context):
    await send_image(update, context, "gpt")
    message = load_message("gpt")
    await update.message.reply_text(
        message,
        reply_markup=gpt_keyboard()
    )
    return GPT_DIALOG

async def gpt_dialog(update, context):
    text = update.message.text
    if text == "❌ Вийти з GPT":
        await update.message.reply_text(
            "Діалог завершено",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    prompt = load_prompt("gpt")
    chat_gpt = ChatGptService(config.OPENAI_TOKEN)
    answer = await chat_gpt.send_question(prompt, text)
    await update.message.reply_text(answer)
    return GPT_DIALOG

async def cancel(update, context):
    await send_text(update, context, "Діалог завершено")
    return ConversationHandler.END


async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DOCS = load_instructions()
    if not update.message or not update.message.text:
        return
    if update.message.from_user.is_bot: # перевіряємо що повідомлення не від іншого бота
        return
    text = update.message.text.lower()
    bot_username = context.bot.username.lower() # --- 1. перевірка згадки бота ---
    if f"@{bot_username}" in text:
        should_answer = True
    else:
        keywords = ["baf", "crm", "логін", "доступ", "система"] # --- 2. перевірка ключових слів ---
        if any(word in text for word in keywords):
            should_answer = True
        else:
            should_answer = False
    chat_gpt = ChatGptService(config.OPENAI_TOKEN)
    if not should_answer:
        return
    prompt = load_prompt("work_assistant") + f"\n\nІнструкції компанії:\n{DOCS}"
    answer = await chat_gpt.send_question(prompt, text)
    await asyncio.sleep(3)
    await update.message.reply_text(answer)


gpt_handler = ConversationHandler(
    entry_points=[CommandHandler("gpt", gpt)],
    states={
        GPT_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_dialog)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
)

async def error_handler(update, context):
    logging.error("Виникло виключення під час опрацювання оновлення (update):", exc_info=context.error)



def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # обробники команди:
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('random', random))


    app.add_handler(gpt_handler)
    app.add_handler(get_profile_conversation_handler())
    # app.add_handler(get_movie_conversation_handler())

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message))

    app.add_error_handler(error_handler)

    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()