FROM python:3.9

WORKDIR /myapi

# 최신 pip 설치
RUN pip install --upgrade pip

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY ./myapi /myapi

# 환경 변수 설정
ENV MONGO_URI=mongodb://mongo:27017

# Uvicorn을 사용하여 FastAPI 애플리케이션 실행
CMD ["uvicorn", "myapi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
