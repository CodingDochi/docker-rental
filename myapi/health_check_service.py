import asyncio
import psutil  # 시스템 상태 확인을 위한 라이브러리
from myapi.database import health_collection
from datetime import datetime

async def start_health_check():
    while True:
        await send_health_check()
        await asyncio.sleep(60)  # 1분마다 체크

async def send_health_check():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    
    health_doc = {
        "cpu_usage": cpu,
        "memory_usage": memory.percent,
        "timestamp": datetime.utcnow()
    }
    
    await health_collection.insert_one(health_doc)
    
    if cpu > 80 or memory.percent > 80:
        print("Warning: High CPU or Memory usage!")
    else:
        print("Health check passed.")
