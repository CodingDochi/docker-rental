from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Optional
from datetime import datetime

from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return handler(ObjectId)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: JsonSchemaValue, handler) -> JsonSchemaValue:
        schema['type'] = 'string'
        return schema
    
# User 모델 정의
class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    password: str

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# ServerRental 모델 정의
class ServerRental(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    image: str
    container_id: Optional[str]
    status: str  # active, saved, discarded
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
