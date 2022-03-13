FROM python:3.10-slim-bullseye

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]