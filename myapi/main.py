from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

async def lifespan_handler(app: FastAPI):
    # MongoDB 클라이언트 연결 설정
    app.mongodb_client = AsyncIOMotorClient("mongodb://mongo:27017")
    app.mongodb = app.mongodb_client["docker_rental"]
    yield
    # 애플리케이션 종료 시 MongoDB 클라이언트 연결 종료
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan_handler)

# /health 엔드포인트 추가
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 라우터 등록
from myapi.container_controller import container_router
from myapi.user_controller import user_router
app.include_router(container_router, prefix="/containers")
app.include_router(user_router, prefix="/auth")
