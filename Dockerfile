FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential libffi-dev libxml2 libxml2-dev libxslt1-dev \
    libjpeg-dev zlib1g-dev libpangocairo-1.0-0 libcairo2 && apt-get clean
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--log-level", "info"]
