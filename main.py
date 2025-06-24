
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7820703898:AAFALGxcLTQ_DYfBJbWelzROlW1rjGFyT8M"
MATIC_API_KEY = "matic-i8Y7oXTrpHFnVJa5IV"

# Kategori dan layanan
KATEGORI = {
    "E-Wallet": ["DANA", "OVO", "ShopeePay", "GoPay", "GoPay Driver", "Grab", "Grab Driver", "LinkAja", "I-Saku", "SEMUA CEK"],
    "Gaming": ["Free Fire", "Mobile Legends", "PUBG"],
    "Tagihan": ["PLN Pascabayar", "PLN Prabayar"]
}

# Endpoint tiap layanan
ENDPOINTS = {
    "DANA": "/api/check-dana",
    "OVO": "/api/check-ovo",
    "ShopeePay": "/api/check-shopeepay",
    "GoPay": "/api/check-gopay",
    "GoPay Driver": "/api/check-gopay-driver",
    "Grab": "/api/check-grab-penumpang",
    "Grab Driver": "/api/check-grab-driver",
    "LinkAja": "/api/check-linkaja",
    "I-Saku": "/api/check-isaku",
    "Free Fire": "/api/check-ff",
    "Mobile Legends": "/api/check-ml",
    "PUBG": "/api/check-pubg",
    "PLN Pascabayar": "/api/check-pln",
    "PLN Prabayar": "/api/check-pln-prabayar"
}

user_state = {}

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(k, callback_data=k)] for k in KATEGORI.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih kategori layanan:", reply_markup=reply_markup)

# Handler kategori
async def handle_kategori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kategori = query.data
    keyboard = [[InlineKeyboardButton(tipe, callback_data=tipe)] for tipe in KATEGORI[kategori]]
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="KEMBALI")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Pilih layanan dalam kategori *{kategori}*:", reply_markup=reply_markup, parse_mode="Markdown")

# Handler layanan
async def handle_layanan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipe = query.data

    if tipe == "KEMBALI":
        return await start(update, context)

    context.user_data["tipe"] = tipe

    if tipe == "SEMUA CEK":
        await query.edit_message_text("Kirim nomor HP untuk dicek di semua layanan:")
    else:
        await query.edit_message_text(f"Kirim nomor untuk dicek di layanan *{tipe}*:", parse_mode="Markdown")

# Handler input nomor
async def handle_nomor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text.strip()

    if not data.isdigit():
        await update.message.reply_text("⚠️ Harap masukkan nomor yang valid.")
        return

    tipe = context.user_data.get("tipe")

    if not tipe:
        await update.message.reply_text("Silakan mulai dari /start.")
        return

    if tipe == "SEMUA CEK":
        for layanan in KATEGORI["E-Wallet"]:
            if layanan == "SEMUA CEK":
                continue
            await cek_layanan(update, layanan, data)
    else:
        await cek_layanan(update, tipe, data)

# Fungsi panggil API
async def cek_layanan(update: Update, tipe, data):
    endpoint = ENDPOINTS.get(tipe)
    if not endpoint:
        await update.message.reply_text("❌ Layanan tidak ditemukan.")
        return

    url = f"https://matic.eu.org{endpoint}"
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {MATIC_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"phone_number": data}
        )
        hasil = response.json()
        if hasil.get("status") == "success":
            nama = hasil.get("message") or hasil.get("name")
            await update.message.reply_text(f"✅ *{tipe}*:
`{nama}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Data tidak ditemukan untuk *{tipe}*", parse_mode="Markdown")

    except Exception as e:
        logging.exception("Gagal menghubungi API:")
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# Main App
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^KEMBALI$"))
    app.add_handler(CallbackQueryHandler(handle_kategori, pattern="^(" + "|".join(KATEGORI.keys()) + ")$"))
    app.add_handler(CallbackQueryHandler(handle_layanan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nomor))
    print("🤖 Bot kategori siap jalan...")
    app.run_polling()
