from pydantic import BaseModel


class preprocessResponse(BaseModel):
    source: str
    text: str