from fastapi import APIRouter, HTTPException
from myapi.models import User
from myapi.database import user_collection, server_collection
from pydantic import BaseModel
from passlib.context import CryptContext
from bson import ObjectId  # MongoDB에서 ObjectId를 처리
import docker
import datetime

user_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
client = docker.from_env()

class UserCreate(BaseModel):
    user_id: str
    password: str

class UserLogin(BaseModel):
    user_id: str
    password: str

# 사용자 회원가입
@user_router.post("/signup", response_model=User)
async def signup(user: UserCreate):
    existing_user = await user_collection.find_one({"user_id": user.user_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    user_doc = {"user_id": user.user_id, "password": hashed_password}
    result = await user_collection.insert_one(user_doc)
    return User(id=result.inserted_id, user_id=user.user_id, password=hashed_password)

# 사용자 로그인
@user_router.post("/login")
async def login(user: UserLogin):
    user_doc = await user_collection.find_one({"user_id": user.user_id})
    if not user_doc or not pwd_context.verify(user.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # MongoDB ObjectId 대신 입력한 user_id 반환
    return {"success": True, "user_id": user_doc["user_id"]}


# 서버 렌탈 요청
@user_router.post("/request_rent_server")
async def request_rent_server(user_id: str, image: str):
    image = image.strip()
    user_id = user_id.strip()

    existing_user = await user_collection.find_one({"user_id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    server_doc = {
        "user_id": user_id,
        "image": image,
        "status": "pending",  # 어드민 승인을 대기 중
        "created_at": datetime.datetime.utcnow(),
    }
    try:
        result = await server_collection.insert_one(server_doc)
        return {"success": True, "message": "Server rental request submitted. Waiting for admin approval."}
    except Exception as e:
        print(f"문서 삽입 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="Server rental request failed")


# 사용자가 자신의 서버 목록을 조회
@user_router.get("/my_servers/{user_id}")
async def get_user_servers(user_id: str):
    # 모든 상태의 서버를 조회 (pending, active, saved)
    user_servers = await server_collection.find({
        "user_id": user_id,
        "status": {"$in": ["pending", "active", "saved"]}
    }).to_list(100)

    if not user_servers:
        raise HTTPException(status_code=404, detail="No servers found for this user")

    # MongoDB ObjectId 및 Docker 컨테이너 ID를 포함하여 응답
    for server in user_servers:
        server["_id"] = str(server["_id"])  # MongoDB ObjectId를 문자열로 변환
        # MongoDB ObjectId와 Docker 컨테이너 ID 둘 다 리턴
        server["server_mongo_id"] = server["_id"]
        if "container_id" not in server:
            server["container_id"] = "No container assigned"  # 컨테이너가 아직 없을 경우

    return {"servers": user_servers}


# 서버 저장
@user_router.post("/save_server")
async def save_server(container_id: str):
    # Docker 컨테이너 ID를 사용하여 컨테이너 가져오기
    try:
        container = client.containers.get(container_id)  # Docker 컨테이너 ID로 컨테이너 가져오기
        container.stop()  # 컨테이너 중지
        # MongoDB에서 해당 컨테이너의 상태 업데이트
        await server_collection.update_one(
            {"container_id": container_id},
            {"$set": {"status": "saved", "updated_at": datetime.datetime.utcnow()}}
        )
        return {"success": True, "message": "Server saved."}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Docker container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 서버 복원 요청
@user_router.post("/request_restore_server")
async def request_restore_server(user_id: str, container_id: str):
    # MongoDB에서 container_id로 서버 문서 찾기
    server_doc = await server_collection.find_one({"container_id": container_id, "status": "saved"})
    
    if not server_doc:
        raise HTTPException(status_code=404, detail="Saved server not found")

    if server_doc["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to restore this server")

    return {"success": True, "message": "Server restoration request submitted. Waiting for admin approval."}

# 서버 폐기
@user_router.post("/discard_server")
async def discard_server(server_mongo_id: str):
    container = client.containers.get(server_mongo_id)
    container.remove(force=True)
    await server_collection.update_one(
        {"server_mongo_id": server_mongo_id},
        {"$set": {"status": "discarded", "updated_at": datetime.datetime.utcnow()}}
    )
    return {"success": True, "message": "Server discarded."}
