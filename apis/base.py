from fastapi import status
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class BaseResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None

def success_response(data=None, message="success"):
    return {
        "code": 0,
        "message": message,
        "data": data
    }

def error_response(code: int, message: str, data=None):
    return {
        "code": code,
        "message": message,
        "data": data
    }
from sqlalchemy import and_,or_
from core.models import Article
def format_search_kw(keyword: str):
    words = keyword.replace("-"," ").replace("|"," ").split(" ")
    rule = or_(*[Article.title.like(f"%{w}%") for w in words])
    return rule