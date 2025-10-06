import os
import requests
import threading
from flask import Flask
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

# === FLASK SERVER (para Render) ===
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 Bot Binance P2P corriendo en Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)

# === FUNCIONES ===
def obtener_anuncios(trade_type: str, rows: int = 10, fiat: str = "VES"):
    payload = {
        "asset": "USDT",
        "fiat": fiat,
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
    precios = [float(a["adv"]["price"]) for a in anuncios if a["adv"].get("price")]
    minimo = min(precios)
    maximo = max(precios)
    promedio = sum(precios) / len(precios)

    titulo = "🟢 *Compradores de USDT*" if trade_type == "BUY" else "🔴 *Vendedores de USDT*"
    lineas = [f"{titulo}\n", "━━━━━━━━━━━━━━━━━━━━━━━"]

    for i, adv in enumerate(anuncios, start=1):
        a = adv["adv"]
        u = adv["advertiser"]
        precio = a.get("price", "N/A")
        usuario = u.get("nickName", "Desconocido")
        min_limit = a.get("minSingleTransAmount", "?")
        max_limit = a.get("maxSingleTransAmount", "?")

        # Filtrar métodos None
        methods = [
            str(m.get("tradeMethodName", "Desconocido"))
            for m in a.get("tradeMethods", [])
            if m.get("tradeMethodName")
        ]

        lineas.append(
            f"*{i}. {usuario}*\n"
            f"💵 Precio: *{precio} Bs*\n"
            f"📉 Límite: {min_limit} - {max_limit}\n"
            f"🏦 Métodos: {', '.join(methods) if methods else 'No especificado'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )

    # Estadísticas
    lineas.append(
        f"📊 *Estadísticas del mercado:*\n"
        f"▫️ Mínimo: {minimo}\n"
        f"▫️ Máximo: {maximo}\n"
        f"▫️ Promedio: {promedio:.2f}"
    )

    return "\n".join(lineas)

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 ¡Bienvenido al *Bot P2P de Binance*!\n\n"
        "📌 *Comandos disponibles:*\n"
        "• /p2pbuy → Ver *compradores* de USDT en VES\n"
        "• /p2psell → Ver *vendedores* de USDT en VES\n"
        "• /help → Mostrar esta ayuda\n\n"
        "⚡ Datos en tiempo real desde Binance P2P"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Usa `/p2pbuy` o `/p2psell` para consultar el mercado en tiempo real.\n"
        "Ejemplo: `/p2pbuy`",
        parse_mode="Markdown"
    )

async def p2pbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anuncios = obtener_anuncios("BUY")
    await update.message.reply_text(formatear(anuncios, "BUY"), parse_mode="Markdown")

async def p2psell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anuncios = obtener_anuncios("SELL")
    await update.message.reply_text(formatear(anuncios, "SELL"), parse_mode="Markdown")

# === MAIN ===
def main():
    # Iniciar Flask en un hilo paralelo
    threading.Thread(target=run_flask).start()

    # Iniciar bot de Telegram
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("p2pbuy", p2pbuy))
    app.add_handler(CommandHandler("p2psell", p2psell))

    print("🤖 Bot corriendo en Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()
