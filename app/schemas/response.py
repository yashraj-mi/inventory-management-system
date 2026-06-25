from typing import Generic, TypeVar
from pydantic import BaseModel

# Create a TypeVar to hold the specific schema type for 'data'
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None
