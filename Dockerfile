FROM python:3.12-slim

# LibreOffice para exportar a PDF con fidelidad exacta
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 9100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9100", "--reload"]
