FROM python:3.11

WORKDIR /app

COPY ./app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

# ✨ [수정] "app.main:app" -> "main:app" 으로 경로 수정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
