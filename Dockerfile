# Força o uso do Python 3.10 (Versão que a Quotex aceita)
FROM python:3.10-slim

# Instala ferramentas do sistema necessárias para compilar coisas
RUN apt-get update && apt-get install -y git build-essential

# Define a pasta de trabalho
WORKDIR /app

# Copia seus arquivos para dentro da caixa
COPY . .

# Atualiza o pip e instala as dependências
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Comando para iniciar o bot
CMD ["python", "app.py"]
