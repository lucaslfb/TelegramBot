import logging
import os
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Load .env archive
load_dotenv()

# Read .env token
token = os.getenv("TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

OPTIONS, INFORMATIONS_PROJECT, PHOTO, EMAIL = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their options."""
    user = update.message.from_user
    logger.info("Started by: %s", user.first_name)

    reply_keyboard = [["Orçamento", "Ver projetos"]]

    await update.message.reply_text(
        "Olá! Eu sou o *BezerraBot*\U0001F916 e estou aqui para auxiliar você com seu projeto.\n\n"
        "É possível fazer um orçamento, mas se quiser pode olhar alguns projetos já feitos.\n\n"
        "Toque aqui -> /cancelar <- para encerrar a conversa, caso seja um engano.",

    parse_mode=ParseMode.MARKDOWN,
    reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Orçamento ou Ver projetos?"
        ),
    )

    return OPTIONS


async def budget_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected option(budget/projects) and asks for a budget."""
    user = update.message.from_user
    logger.info("Option of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Por favor conte-me mais sobre o que tem em mente.\n\n"
        "Seu projeto pode ter muitas funcionalidades, especifique bem.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return INFORMATIONS_PROJECT


async def see_projects_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected option(budget/projects) and asks about return."""
    user = update.message.from_user
    logger.info("Option of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Bom em saber que você deseja conhecer mais do meu trabalho. É só clicar no link abaixo.\n"
        "Portifólio_de_projetos.com.br.\n\n"
        "Caso queira, pode retornar ao /inicio.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def client_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the budget and asks for a photo."""
    user = update.message.from_user
    logger.info("Budget of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Se quiser pode enviar um foto que te inspirou nesse projeto, assim o processo de criação é acelerado.\n\n"
        "Caso não tenha, basta /pular."
    )

    return PHOTO


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for an email."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()

    if not os.path.exists("photos"):
        os.makedirs("photos")

    file_path = os.path.join("photos", f"{user.first_name}_budget_photo.jpg")

    await photo_file.download_to_drive(file_path)
    logger.info("Photo of %s: %s", user.first_name, "budget_photo.jpg")
    await update.message.reply_text(
        "Agora, envie um email para contato."
    )

    return EMAIL


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for an email."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text(
        "Ok, agora envie um email para contato."
    )

    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the email and ends the conversation."""
    user = update.message.from_user
    user_email = update.message.text
    logger.info(
        "Email of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Ótimo, agora basta esperar, entraremos em contato para acertar prazos e valores.\n\n"
        "Muito obrigado!"
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Poxa! Espero que volte, até mais!",

        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Add conversation handler with the states OPTIONS, INFORMATIONS_PROJECT, PHOTO and EMAIL
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("inicio", start)],
        states={
            OPTIONS: [MessageHandler(filters.Regex("^(Orçamento)$"), budget_option),
                      MessageHandler(filters.Regex("^(Ver projetos)$"), see_projects_option)],
            INFORMATIONS_PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_budget)],
            PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("pular", skip_photo)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    application.add_handler(conv_handler)

    # Receive events updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
