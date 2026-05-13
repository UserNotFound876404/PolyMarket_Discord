FROM python:3.10-slim

WORKDIR /app

# Make sure this matches the filename in your file list exactly
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
