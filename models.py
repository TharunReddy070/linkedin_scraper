from pydantic import BaseModel
from typing import Optional

class LinkedInProfile(BaseModel):
    name: str
    about: Optional[str] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
