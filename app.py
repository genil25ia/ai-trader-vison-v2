if preco_anterior < ma_m1.iloc[-2] and preco_atual > ma_m1.iloc[-1]:
        gatilho = 1 
    # Cruzamento para baixo (Preço anterior acima, preço atual abaixo da MA7)
    elif preco_anterior > ma_m1.iloc[-2] and preco_atual < ma_m1.iloc[-1]:
        gatilho = -1 
        
    # --- DECISÃO FINAL: ALINHAMENTO SNIPER ---
    if tendencia == 1 and forca == 1 and gatilho == 1:
        # Tendência de Alta + Sobrevenda (Pronto para subida) + Gatilho de Compra
        return "COMPRA", "Tendência M15: Alta, Força M5: Sobrevenda, Gatilho M1: Cruzamento p/ Cima"
    elif tendencia == -1 and forca == -1 and gatilho == -1:
        # Tendência de Baixa + Sobrecompra (Pronto para queda) + Gatilho de Venda
        return "VENDA", "Tendência M15: Baixa, Força M5: Sobrecompra, Gatilho M1: Cruzamento p/ Baixo"
    else:
        return "NAO OPERAR", "Aguardando alinhamento M15/M5/M1."


# --- FUNÇÃO PRINCIPAL ASYNC (Loop 24/7) ---
async def main_loop():
    
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, QUOTEX_EMAIL, QUOTEX_PASSWORD]):
        print("ERRO: Variáveis de ambiente (secrets) não configuradas. Verifique o Railway.")
        return

    # Inicializa o cliente da Quotex
    client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, lang="pt")
    
    try:
        await client.connect()
        if not client.check_connect():
            print("ERRO: Falha ao conectar na Quotex. O bot será encerrado.")
            return

        print("Conexão Quotex estabelecida. Iniciando monitoramento 24/7...")

        while True:
            # 1. Obtém os dados de mercado
            df_m15, df_m5, df_m1 = await obter_dados_mercado(client)
            
            # 2. Gera o sinal
            acao, detalhe = gerar_sinal_chefao(df_m15, df_m5, df_m1)
            
            # 3. Envia o sinal apenas se for para Comprar ou Vender
            if acao in ["COMPRA", "VENDA"]:
                enviar_sinal(detalhe, acao)
            else:
                 print(f"Status: {acao} | {detalhe}")
            
            # O loop espera 60 segundos (1 minuto) para verificar o novo candle
            await asyncio.sleep(60)

    except Exception as e:
        print(f"ERRO CRÍTICO NO LOOP PRINCIPAL: {e}")
        # Tenta reconectar após um tempo
        await asyncio.sleep(300) 
        
    finally:
        await client.close()
        print("Bot encerrado.")

if name == "main":
    asyncio.run(main_loop())
