from fastapi import APIRouter, HTTPException
from myapi.database import server_collection
import docker
import datetime
from bson import ObjectId

container_router = APIRouter()
client = docker.from_env()

# 어드민이 서버 생성 요청 목록 확인
@container_router.get("/pending_requests")
async def list_pending_requests():
    pending_requests = await server_collection.find({"status": "pending"}).to_list(100)
    
    # ObjectId를 문자열로 변환
    for request in pending_requests:
        request["_id"] = str(request["_id"])
    
    return {"pending_requests": pending_requests}

# 어드민이 저장된 서버 목록 확인
@container_router.get("/saved_servers")
async def list_saved_servers():
    saved_servers = await server_collection.find({"status": "saved"}).to_list(100)
    
    # ObjectId를 문자열로 변환
    for server in saved_servers:
        server["_id"] = str(server["_id"])
    
    return {"saved_servers": saved_servers}

# 어드민이 서버 생성 (사용자 요청 승인)
@container_router.post("/approve_rent/{server_mongo_id}")
async def approve_rent(server_mongo_id: str):
    server_mongo_id = server_mongo_id.strip()
    request_doc = await server_collection.find_one({"_id": ObjectId(server_mongo_id)})
    if not request_doc or request_doc["status"] != "pending":
        raise HTTPException(status_code=404, detail="Pending server request not found")

    try:
        container = client.containers.run(request_doc["image"], detach=True)
        await server_collection.update_one(
            {"_id": ObjectId(server_mongo_id)},
            {"$set": {"server_mongo_id": container_id, "status": "active", "updated_at": datetime.datetime.utcnow()}}
        )
        return {"success": True, "message": f"Server {container_id} created for {request_doc['user_id']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server creation failed: {str(e)}")

# 어드민이 저장된 서버 복원 (사용자가 요청)
@container_router.post("/restore_saved_server/{server_mongo_id}")
async def restore_saved_server(server_mongo_id: str):
    # 서버 복원 로직 구현
    pass

# 어드민이 서버 요청 거절
@container_router.post("/reject_rent/{server_mongo_id}")
async def reject_rent(server_mongo_id: str):
    request_doc = await server_collection.find_one({"_id": ObjectId(server_mongo_id)})
    if not request_doc or request_doc["status"] != "pending":
        raise HTTPException(status_code=404, detail="Pending server request not found")
    
    await server_collection.update_one(
        {"_id": ObjectId(server_mongo_id)},
        {"$set": {"status": "rejected", "updated_at": datetime.datetime.utcnow()}}
    )
    return {"success": True, "message": "Server rental request rejected."}

# 어드민이 전체 컨테이너 상태 확인
@container_router.get("/all_containers")
async def list_all_containers():
    containers = client.containers.list(all=True)  # 모든 컨테이너 확인
    container_data = []
    for container in containers:
        container_data.append({
            "id": container.id,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "status": container.status,
        })
    return {"containers": container_data}

# 특정 컨테이너 강제 중지
@container_router.post("/stop_container/{container_id}")
async def stop_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.stop()
        await server_collection.update_one({"server_mongo_id": container_id}, {"$set": {"status": "stopped"}})
        return {"success": True, "message": f"Container {container_id} stopped."}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")

# 특정 컨테이너 강제 삭제
@container_router.delete("/delete_container/{container_id}")
async def delete_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
        await server_collection.update_one({"server_mongo_id": container_id}, {"$set": {"status": "deleted"}})
        return {"success": True, "message": f"Container {container_id} deleted."}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
