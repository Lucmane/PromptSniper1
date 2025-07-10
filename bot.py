import logging
import os
import json
import tempfile

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from gradio_client import Client
from dotenv import load_dotenv

# Charger les variables d'environnement (.env ou Render Dashboard)
load_dotenv()

# ============ CONFIG ============
TELEGRAM_TOKEN = "7853973479:AAFH_1G40ULASUznLAOOglJCd0zyg5xPnd8"
CLIP_API_URL = "https://pharmapsychotic-clip-interrogator.hf.space/"
CLIP_MODEL = "ViT-L (best for Stable Diffusion 1.*)"
CLIP_MODE = "best"
CHANNEL_USERNAME = "@ctrl_future"
USER_DB_PATH = "users.json"

client = Client(CLIP_API_URL)

# ============ LOGGING ============
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ UTILS ============
def load_users():
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'r') as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(list(users), f)

verified_users = load_users()

# ============ BOT COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_users:
        await update.message.reply_text("✅ Tu es déjà vérifié. Envoie-moi une image pour générer un prompt !")
        return

    keyboard = [[InlineKeyboardButton("✅ J’ai rejoint le canal", callback_data="check_subscription")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Yo dev sniper, bienvenue sur *PromptSniper*\n\n"
        "🚧 Avant de générer des prompts d’élite, tu dois rejoindre notre QG :\n"
        "👉 [CTRL+FUTURE](https://t.me/ctrl_future) — *le canal où on construit le futur (IA, dev, automation & délire tech)*\n\n"
        "🎁 Tu y découvriras des outils, bots, API secrètes et projets exclusifs.\n\n"
        "Une fois que c’est fait, clique sur le bouton ci-dessous :",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'creator', 'administrator']:
            verified_users.add(user_id)
            save_users(verified_users)
            await query.edit_message_text("✅ Vérifié avec succès ! Envoie-moi une image pour sniper un prompt !")
        else:
            await query.edit_message_text("❌ Tu n'as pas encore rejoint le canal. Rejoins [CTRL+FUTURE](https://t.me/ctrl_future) puis réessaie.", parse_mode='Markdown')
    except Exception as e:
        logger.error(e)
        await query.edit_message_text("❌ Erreur lors de la vérification. Réessaie plus tard.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in verified_users:
        await update.message.reply_text("🔐 Tu dois rejoindre notre canal CTRL+FUTURE pour utiliser ce bot.", parse_mode='Markdown')
        return

    try:
        photo_file = await update.message.photo[-1].get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
            await photo_file.download_to_drive(tf.name)
            tf.flush()
            detailed_result = client.predict(tf.name, CLIP_MODEL, fn_index=1)
            simple_result = client.predict(tf.name, CLIP_MODEL, CLIP_MODE, fn_index=3)

        prompt = simple_result[0]
        artist = detailed_result[1]
        style = detailed_result[2]
        trending = detailed_result[3]
        flavor = detailed_result[4]

        reply_text = (
            f"🎯 *PromptSniper a tiré :*\n\n"
            f"`{prompt}`\n\n"
            f"🧠 *Résumé artistique :*\n"
            f"• 🎨 Style : {style}\n"
            f"• 👨‍🎨 Artiste : {artist}\n"
            f"• 📈 Tendance : {trending}\n"
            f"• 🍭 Ambiance : {flavor}\n\n"
            f"_Powered by PromptSniper x CTRL+FUTURE_ 🔫"
        )

        await update.message.reply_text(reply_text, parse_mode='Markdown')
        os.remove(tf.name)

    except Exception as e:
        logger.error(f"Erreur : {e}")
        await update.message.reply_text("❌ Une erreur est survenue. Essaie encore.")

async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Je ne fonctionne qu’avec des images. Envoie-moi une photo pour générer un prompt !")

# ============ MAIN ============
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(~filters.PHOTO, handle_other))
    logger.info("🤖 PromptSniper is live and hunting...")
    app.run_polling()

if __name__ == "__main__":
    main()
