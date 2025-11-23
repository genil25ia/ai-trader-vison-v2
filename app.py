import asyncio
import os
import requests
import pandas as pd
import pandas_ta as ta  # <--- MUDANÇA AQUI
from datetime import datetime

# Importação da biblioteca da Quotex
from pyquotex.stable_api import Quotex

# --- CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
QUOTEX_EMAIL = os.environ.get("QUOTEX_EMAIL")
QUOTEX_PASSWORD = os.environ.get("QUOTEX_PASSWORD")

ATIVO = "EURUSD"

# --- FUNÇÃO: ENVIAR SINAL VIA TELEGRAM ---
def enviar_sinal(mensagem, acao):
    emoji = "🟢" if acao == "COMPRA" else "🔴" if acao == "VENDA" else "🟡"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': f"{emoji} *SINAL SNIPER V2.0 (Pandas-TA)*\n\n"
                f"📊 Ativo: {ATIVO}\n"
                f"⏰ Horário: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📈 Ação: *{acao}*\n\n"
                f"Detalhe: {mensagem}",
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload)
        print(f"Sinal enviado: {acao}")
    except Exception as e:
        print(f"Erro Telegram: {e}")

# --- FUNÇÃO: OBTENÇÃO DE DADOS ---
async def obter_dados_mercado(client: Quotex):
    print(f"Buscando dados {ATIVO}...")
    try:
        # Pega mais velas para garantir o cálculo correto
        candles_m15 = await client.get_candles(ATIVO, "M15", 200)
        candles_m5 = await client.get_candles(ATIVO, "M5", 200)
        candles_m1 = await client.get_candles(ATIVO, "M1", 200)
        
        # Cria DataFrames
        df_m15 = pd.DataFrame({'close': [c.close for c in candles_m15]})
        df_m5 = pd.DataFrame({'close': [c.close for c in candles_m5]})
        df_m1 = pd.DataFrame({'close': [c.close for c in candles_m1]})

        return df_m15, df_m5, df_m1
    except Exception as e:
        print(f"Erro Quotex: {e}")
        return None, None, None

# --- FUNÇÃO: LÓGICA DO SINAL (ADAPTADA PARA PANDAS_TA) ---
def gerar_sinal_chefao(df_m15, df_m5, df_m1):
    if df_m15 is None: return "Erro", "Sem dados"

    # 1. TENDÊNCIA M15 (Média Móvel Simples 50)
    # A biblioteca pandas_ta adiciona o método .ta ao DataFrame
    sma_m15 = df_m15.ta.sma(length=50)
    if sma_m15 is None or sma_m15.iloc[-1] is None: return "Aguardando", "Calculando MAs"
    
    tendencia = 1 if df_m15['close'].iloc[-1] > sma_m15.iloc[-1] else -1

    # 2. FORÇA M5 (RSI 14)
    rsi_m5 = df_m5.ta.rsi(length=14)
    if rsi_m5 is None: return "Aguardando", "Calculando RSI"
    
    forca = 0
    if rsi_m5.iloc[-1] > 70: forca = -1 # Sobrecomprado
    elif rsi_m5.iloc[-1] < 30: forca = 1 # Sobrevendido

    # 3. GATILHO M1 (Cruzamento MA7)
    sma_m1 = df_m1.ta.sma(length=7)
    if sma_m1 is None: return "Aguardando", "Calculando MA7"

    preco_atual = df_m1['close'].iloc[-1]
    preco_ant = df_m1['close'].iloc[-2]
    ma_atual = sma_m1.iloc[-1]
    ma_ant = sma_m1.iloc[-2]
    
    gatilho = 0
    if preco_ant < ma_ant and preco_atual > ma_atual: gatilho = 1 # Cruzou pra cima
    elif preco_ant > ma_ant and preco_atual < ma_atual: gatilho = -1 # Cruzou pra baixo

    # DECISÃO
    if tendencia == 1 and forca == 1 and gatilho == 1:
        return "COMPRA", "Tendência Alta + RSI Baixo + Gatilho Up"
    elif tendencia == -1 and forca == -1 and gatilho == -1:
        return "VENDA", "Tendência Baixa + RSI Alto + Gatilho Down"
    else:
        return "NAO OPERAR", f"Sinais mistos. T:{tendencia} F:{forca} G:{gatilho}"

# --- LOOP PRINCIPAL ---
async def main_loop():
    if not TELEGRAM_BOT_TOKEN:
        print("ERRO: Variáveis não configuradas!")
        return

    client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, lang="pt")
    
    try:
        await client.connect()
            print("Conectado na Quotex!")
        
        while True:
            df_m15, df_m5, df_m1 = await obter_dados_mercado(client)
            acao, detalhe = gerar_sinal_chefao(df_m15, df_m5, df_m1)
            
            if acao in ["COMPRA", "VENDA"]:
                enviar_sinal(detalhe, acao)
            else:
                print(f"Monitorando... {acao}")
            
            await asyncio.sleep(60)

    except Exception as e:
        print(f"Erro fatal: {e}")
        await asyncio.sleep(10)
    finally:
        client.close()

if name == "main":
    asyncio.run(main_loop())
