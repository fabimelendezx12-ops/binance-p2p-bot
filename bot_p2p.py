import requests
import sys
from typing import List, Dict, Any

BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://p2p.binance.com",
    "Referer": "https://p2p.binance.com/en",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def obtener_anuncios(asset: str, fiat: str, trade_type: str, rows: int = 10, page: int = 1) -> List[Dict[str, Any]]:
    payload = {
        "asset": asset,
        "fiat": fiat,
        "tradeType": trade_type,
        "rows": rows,
        "page": page
    }
    response = requests.post(BINANCE_P2P_URL, json=payload, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "data" not in data or not isinstance(data["data"], list):
        raise ValueError("Respuesta inesperada del backend de Binance P2P")

    return data["data"]

def formatear_salida(anuncios: List[Dict[str, Any]], trade_type: str) -> str:
    titulo = f"🔹 Top anuncios P2P (USDT → VES, {trade_type})"
    lineas = [titulo, ""]
    for i, adv in enumerate(anuncios, start=1):
        a = adv["adv"]
        u = adv["advertiser"]
        precio = a.get("price", "?")
        usuario = u.get("nickName", "Desconocido")
        min_limit = a.get("minSingleTransAmount", "?")
        max_limit = a.get("maxSingleTransAmount", "?")
        methods = [m.get("tradeMethodName", "") for m in a.get("tradeMethods", [])]
        linea = f"{i}. {usuario} | Precio: {precio} Bs | Límite: {min_limit}–{max_limit} | Métodos: {', '.join(methods) or 'N/D'}"
        lineas.append(linea)
    return "\n".join(lineas)

def main():
    try:
        if len(sys.argv) < 2:
            print("Usa: python bot_p2p.py /p2pbuy o /p2psell")
            return

        comando = sys.argv[1].lower()

        if comando == "/p2pbuy":
            trade_type = "BUY"
        elif comando == "/p2psell":
            trade_type = "SELL"
        else:
            print("Comando no reconocido. Usa /p2pbuy o /p2psell")
            return

        anuncios = obtener_anuncios("USDT", "VES", trade_type, rows=10, page=1)

        # 👇 Ajuste clave: BUY ascendente, SELL descendente
        if trade_type == "SELL":
            anuncios_ordenados = sorted(anuncios, key=lambda x: float(x["adv"]["price"]), reverse=True)
        else:  # BUY
            anuncios_ordenados = sorted(anuncios, key=lambda x: float(x["adv"]["price"]))

        salida = formatear_salida(anuncios_ordenados, trade_type)
        print(salida)

    except requests.HTTPError as e:
        print(f"Error HTTP: {e} | Detalle: {getattr(e.response, 'text', '')[:300]}")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    main()
