from typing import Optional
from pydantic import BaseModel

# Model for profile response
class UserResponse(BaseModel):
    id: Optional[str]
    name: str
    email: str

# Model for updating the password
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
