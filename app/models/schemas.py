from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="ข้อความที่ต้องการให้สร้างภาพ", min_length=1)
    style: Optional[str] = Field(None, description="สไตล์ของภาพ เช่น 'photorealistic', 'cinematic', 'anime'")
    aspect_ratio: Optional[str] = Field("1:1", description="สัดส่วนภาพ เช่น '1:1', '16:9'")


class ImageGenerationResponse(BaseModel):
    status: str = Field(..., description="สถานะของการสร้างภาพ")
    from_cache: bool = Field(..., description="true ถ้าดึงมาจาก cache")
    image_url: str = Field(..., description="URL ของรูปภาพที่สร้างเสร็จ")
    created_at: datetime = Field(..., description="เวลาที่สร้างรูปภาพ")


class ErrorResponse(BaseModel):
    status: str = Field("error", description="สถานะข้อผิดพลาด")
    message: str = Field(..., description="รายละเอียดข้อผิดพลาด")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="สถานะของ service")

