from typing import Optional
from pydantic import BaseModel

class File(BaseModel):
    id: Optional[str]
    user_id: str  # Relación con el usuario
    file_name: str
