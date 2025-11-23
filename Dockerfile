# Usar Python 3.10 oficial (que a Quotex aceita)
FROM python:3.10-slim

# Instala ferramentas do sistema necessárias
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    ca-certificates # <--- NOVO: Instala os certificados de segurança!

# Define a pasta de trabalho
WORKDIR /app

# Copia os arquivos
COPY . .

# Atualiza o pip e instala as dependências
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar
CMD ["python", "app.py"]
