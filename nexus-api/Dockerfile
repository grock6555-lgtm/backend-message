FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Копируем библиотеку (если не используем volume)
COPY libnexus_crypto.so /app/libnexus_crypto.so
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]