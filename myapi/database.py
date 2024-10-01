from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db: str = "docker_rental"

    class Config:
        env_file = ".env"

settings = Settings()

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]

# 컬렉션 정의
user_collection = db.get_collection("users")
server_collection = db.get_collection("servers")
health_collection = db.get_collection("health_checks")  # health_collection 추가
