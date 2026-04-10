from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar('T')


@dataclass(slots=True)
class ServiceResult(Generic[T]):
    ok: bool
    value: T | None = None
    code: str | None = None
    message: str | None = None
    details: dict[str, object] = field(default_factory=dict)
