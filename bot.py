import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Defina no Railway
CHAT_ID = 1474097769                # Seu ID fixo
MONITORANDO = False

URL = "https://historicosblaze.com/blaze/doubles"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot ativo! Use /monitorar para começar e /parar para parar.")

async def monitorar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MONITORANDO
    MONITORANDO = True
    await update.message.reply_text("🔍 Iniciando monitoramento...")
    asyncio.create_task(monitorar_loop(context.application))

async def parar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MONITORANDO
    MONITORANDO = False
    await update.message.reply_text("⛔ Monitoramento parado.")

async def monitorar_loop(app: Application):
    global MONITORANDO
    combinacoes_previstas = []

    while MONITORANDO:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")

            linhas = soup.select("tr")  # cada linha tem hora e número
            historico = []
            for linha in linhas[1:]:  # pula cabeçalho
                cols = linha.find_all("td")
                if len(cols) >= 2:
                    hora = cols[0].text.strip()
                    try:
                        numero = int(cols[1].text.strip())
                    except:
                        continue
                    historico.append((hora, numero))

            historico = historico[::-1]  # mais antigo para mais recente

            # Procura brancos e gera combinações
            for i, (hora, num) in enumerate(historico):
                if num == 0:  # branco
                    anteriores = [historico[j][1] for j in range(max(0, i-2), i)]
                    posteriores = [historico[j][1] for j in range(i+1, min(len(historico), i+3))]

                    combs = []
                    if len(anteriores) >= 2:
                        combs.append(sum(anteriores))
                    if len(posteriores) >= 2:
                        combs.append(sum(posteriores))
                    if len(anteriores) >= 1 and len(posteriores) >= 1:
                        combs.append(anteriores[0] + posteriores[0])
                    if len(anteriores) + len(posteriores) >= 3:
                        combs.append(sum(anteriores + posteriores[:1]))
                    if len(anteriores) + len(posteriores) == 4:
                        combs.append(sum(anteriores + posteriores))

                    for c in combs:
                        if c not in combinacoes_previstas:
                            combinacoes_previstas.append(c)

            # Verifica se último número bate com previsão
            if historico[-1][1] in combinacoes_previstas:
                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚪ Possível branco previsto! Número atual {historico[-1][1]} bate com combinação."
                )

        except Exception as e:
            await app.bot.send_message(chat_id=CHAT_ID, text=f"Erro: {e}")

        await asyncio.sleep(15)  # intervalo entre checagens

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("monitorar", monitorar_cmd))
    app.add_handler(CommandHandler("parar", parar_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
