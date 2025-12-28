from pydantic import BaseModel

class CaptionRequest(BaseModel):
    caption: str
    tone: str = "casual"