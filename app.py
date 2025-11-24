import asyncio
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Importação da biblioteca da Quotex
#from quotexapi.stable_api import Quotex

# --- CONFIGURAÇÃO DE VARIÁVEIS ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
QUOTEX_EMAIL = os.environ.get("QUOTEX_EMAIL")
QUOTEX_PASSWORD = os.environ.get("QUOTEX_PASSWORD")
ATIVO = "EURUSD"

# --- FUNÇÕES MATEMÁTICAS (SUBSTITUINDO AS BIBLIOTECAS) ---
def calcular_sma(series, periodo):
    """Calcula Média Móvel Simples (SMA)"""
    return series.rolling(window=periodo).mean()

def calcular_rsi(series, periodo=14):
    """Calcula RSI manualmente"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- FUNÇÃO: ENVIAR SINAL VIA TELEGRAM ---
def enviar_sinal(mensagem, acao):
    emoji = "🟢" if acao == "COMPRA" else "🔴" if acao == "VENDA" else "🟡"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': f"{emoji} *SINAL SNIPER (NATIVO)*\n\n"
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
        # Busca velas suficientes para o cálculo manual
        candles_m15 = await client.get_candles(ATIVO, "M15", 200)
        candles_m5 = await client.get_candles(ATIVO, "M5", 200)
        candles_m1 = await client.get_candles(ATIVO, "M1", 200)
        
        df_m15 = pd.DataFrame({'close': [c.close for c in candles_m15]})
        df_m5 = pd.DataFrame({'close': [c.close for c in candles_m5]})
        df_m1 = pd.DataFrame({'close': [c.close for c in candles_m1]})

        return df_m15, df_m5, df_m1
    except Exception as e:
        print(f"Erro Quotex: {e}")
        return None, None, None

# --- FUNÇÃO: LÓGICA DO SINAL ---
def gerar_sinal_chefao(df_m15, df_m5, df_m1):
    if df_m15 is None: return "Erro", "Sem dados"

    # 1. TENDÊNCIA M15 (SMA 50)
    sma_m15 = calcular_sma(df_m15['close'], 50)
    if pd.isna(sma_m15.iloc[-1]): return "Aguardando", "Calculando MAs"
    
    tendencia = 1 if df_m15['close'].iloc[-1] > sma_m15.iloc[-1] else -1

    # 2. FORÇA M5 (RSI 14)
    rsi_m5 = calcular_rsi(df_m5['close'], 14)
    if pd.isna(rsi_m5.iloc[-1]): return "Aguardando", "Calculando RSI"
    
    forca = 0
    if rsi_m5.iloc[-1] > 70: forca = -1 # Sobrecomprado
    elif rsi_m5.iloc[-1] < 30: forca = 1 # Sobrevendido

    # 3. GATILHO M1 (SMA 7)
    sma_m1 = calcular_sma(df_m1['close'], 7)
    if pd.isna(sma_m1.iloc[-1]): return "Aguardando", "Calculando MA7"

    preco_atual = df_m1['close'].iloc[-1]
    preco_ant = df_m1['close'].iloc[-2]
    ma_atual = sma_m1.iloc[-1]
    ma_ant = sma_m1.iloc[-2]
    
    gatilho = 0
    if preco_ant < ma_ant and preco_atual > ma_atual: gatilho = 1 
    elif preco_ant > ma_ant and preco_atual < ma_atual: gatilho = -1 

    # DECISÃO
    if tendencia == 1 and forca == 1 and gatilho == 1:
        return "COMPRA", "Tendência Alta + RSI Baixo + Gatilho Up"
    elif tendencia == -1 and forca == -1 and gatilho == -1:
        return "VENDA", "Tendência Baixa + RSI Alto + Gatilho Down"
    else:
        return "NAO OPERAR", f"Neutro. T:{tendencia} F:{forca} G:{gatilho}"

# --- LOOP PRINCIPAL ---
async def main_loop():
    if not TELEGRAM_BOT_TOKEN:
        print("ERRO: Variáveis não configuradas!")
        return

#PROMPTTEXTO, [23/11/2025 19:53]
# Inicia cliente Quotex
    #client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, lang="pt")
    
    try:
        # Tenta conectar
        status = await client.connect()
        print(f"Tentativa de conexão: {status}")
        
        while True:
            df_m15, df_m5, df_m1 = await obter_dados_mercado(client)
            acao, detalhe = gerar_sinal_chefao(df_m15, df_m5, df_m1)
            
            if acao in ["COMPRA", "VENDA"]:
                enviar_sinal(detalhe, acao)
            else:
                print(f"Monitorando... {acao} | {detalhe}")
            
            await asyncio.sleep(60)

    except Exception as e:
        print(f"Erro fatal: {e}")
        # Reinicia conexão em caso de erro
        await asyncio.sleep(10)
    finally:
        client.close()

if name == "main":
    asyncio.run(main_loop())
