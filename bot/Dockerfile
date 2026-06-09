FROM python:3.11-slim

WORKDIR /app

COPY bot/ /app/bot/
COPY assets/ /app/assets/

RUN pip install --no-cache-dir -r /app/bot/requirements.txt

CMD ["python", "-m", "bot.main"]
