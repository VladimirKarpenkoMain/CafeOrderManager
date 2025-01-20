FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev musl-dev supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY supervisord.conf /etc/supervisord.conf

COPY . /app/

CMD ["supervisord", "-c", "/etc/supervisord.conf"]