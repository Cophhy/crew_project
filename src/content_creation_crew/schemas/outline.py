from pydantic import BaseModel, HttpUrl, Field
from typing import List

class OutlineSection(BaseModel):
    heading: str
    bullet_points: List[str] = Field(min_length=3, max_length=6)
    wikipedia_urls: List[HttpUrl] = Field(min_length=1)

class OutlineModel(BaseModel):
    audience: str
    angle: str
    working_title: str
    tl_dr: str  # 2–3 sentences
    seo_keywords: List[str] = []
    sections: List[OutlineSection] = Field(min_length=3, max_length=5)
