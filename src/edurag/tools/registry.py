from typing import Any, Callable, Awaitable
from edurag.config.logging import logger


class ToolRegistry:
    _tools: dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, func: Callable[..., Any]) -> None:
        cls._tools[name] = func
        logger.info(f"Tool registered: {name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._tools.pop(name, None)

    @classmethod
    def get(cls, name: str) -> Callable[..., Any] | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def get_all(cls) -> dict[str, Callable[..., Any]]:
        return dict(cls._tools)

    @classmethod
    async def execute(cls, name: str, **kwargs: Any) -> Any:
        func = cls._tools.get(name)
        if func is None:
            raise ValueError(f"Tool not found: {name}")
        result = func(**kwargs)
        if hasattr(result, "__await__"):
            result = await result
        return result
