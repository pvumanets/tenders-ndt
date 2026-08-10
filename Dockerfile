FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright deps подтянутся на P1+/P6 через playwright install-deps
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# P0: образ-скелет. API/worker появятся с P1–P5.
CMD ["python", "-c", "print('ndt-tender-scout P0 skeleton — implement API on P5')"]
