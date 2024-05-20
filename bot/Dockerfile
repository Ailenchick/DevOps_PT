# Installig python3
FROM python:3.9-slim

# Setting workdir
WORKDIR /Bot

# Copy requirements.txt to workdir
COPY . .

# Requirements installation
RUN pip install --no-cache-dir -r requirements.txt

# Bot run
CMD ["python", "./Bot.py"]
