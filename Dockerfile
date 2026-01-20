FROM python:3.11-slim

WORKDIR /app

COPY runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY runner .

CMD ["python", "main.py"]
