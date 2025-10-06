import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === CONFIG ===
TOKEN = os.getenv("TOKEN")  # Lo leeremos de variable de entorno
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://p2p.binance.com",
    "Referer": "https://p2p.binance.com/en",
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def obtener_anuncios(trade_type: str, rows: int = 10):
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "rows": rows,
        "page": 1
    }
    r = requests.post(BINANCE_P2P_URL, json=payload, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()["data"]

    # Ordenar según Binance
    if trade_type == "SELL":
        data = sorted(data, key=lambda x: float(x["adv"]["price"]), reverse=True)
    else:  # BUY
        data = sorted(data, key=lambda x: float(x["adv"]["price"]))

    return data

def formatear(anuncios, trade_type):
    lineas = [f"🔹 Top anuncios P2P (USDT → VES, {trade_type})", ""]
    for i, adv in enumerate(anuncios, start=1):
        a = adv["adv"]
        u = adv["advertiser"]
        precio = a["price"]
        usuario = u["nickName"]
        min_limit = a["minSingleTransAmount"]
        max_limit = a["maxSingleTransAmount"]
        methods = [m["tradeMethodName"] for m in a["tradeMethods"]]
        lineas.append(f"{i}. {usuario} | {precio} Bs | Límite: {min_limit}-{max_limit} | Métodos: {', '.join(methods)}")
    return "\n".join(lineas)

# === HANDLERS ===
async def p2pbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anuncios = obtener_anuncios("BUY")
    await update.message.reply_text(formatear(anuncios, "BUY"))

async def p2psell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anuncios = obtener_anuncios("SELL")
    await update.message.reply_text(formatear(anuncios, "SELL"))

# === MAIN ===
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("p2pbuy", p2pbuy))
    app.add_handler(CommandHandler("p2psell", p2psell))
    print("🤖 Bot corriendo en Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()
