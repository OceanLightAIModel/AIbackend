FROM python:3.11

# 1. 작업 디렉토리를 /app 으로 설정
WORKDIR /app

# 2. requirements.txt 파일을 먼저 복사하여 라이브러리 설치
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 나머지 app 폴더의 모든 코드를 복사
COPY ./app .

# 4. 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
