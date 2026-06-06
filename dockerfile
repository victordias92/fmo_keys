FROM python:3.11-slim

# diretório de trabalho
WORKDIR /app

# instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiar código
COPY . .

# expor porta padrão do Flet
EXPOSE 8550

# comando para rodar o app
CMD ["python", "main.py"]
