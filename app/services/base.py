from typing import Any, Generic, TypeVar
from app.repositories.base import BaseRepository

T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Base Service class encapsulating a generic Repository instance for Clean Architecture.
    All business services inherit from this class to obtain repository access.
    """
    def __init__(self, repository: BaseRepository[T]) -> None:
        self.repository = repository
