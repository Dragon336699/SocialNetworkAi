from pydantic import BaseModel

class SummarizePostRequest(BaseModel):
    content: str