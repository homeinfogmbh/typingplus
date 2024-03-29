"""Enhanced type hinting hacks."""

from contextlib import suppress
from typing import _UnionGenericAlias
from typing import Any
from typing import Callable
from typing import ForwardRef
from typing import Iterable
from typing import Optional
from typing import Union


__all__ = ["resolve_type_hints", "resolve_all_type_hints"]


def _resolve_type_hint(value: Any, mapping: dict[str, Any]) -> Any:
    """Resolve a type hint."""

    if isinstance(value, str):
        return mapping.get(value, value)

    if isinstance(value, ForwardRef):
        return _resolve_type_hint(value.__forward_arg__, mapping)

    if isinstance(value, _UnionGenericAlias):
        value.__args__ = tuple(
            _resolve_type_hint(arg, mapping) for arg in value.__args__
        )

    return value


def _resolve_type_hints(annotations: dict[str, Any], mapping: dict[str, Any]) -> None:
    """Resolve type hints of the given annotations' dict."""

    for key, value in dict(annotations).items():
        annotations[key] = _resolve_type_hint(value, mapping)


def _get_attributes(cls: type) -> Iterable[str]:
    """Return attribute names of the class."""

    try:
        return cls.__dict__
    except AttributeError:
        return cls.__slots__


def _resolve_object(obj: Any, mapping: dict[str, Any]) -> None:
    """Resolve type hints of the given attribute."""

    with suppress(AttributeError):
        _resolve_type_hints(obj.__annotations__, mapping)


def _resolve_class(cls: type, mapping: dict[str, Any]) -> None:
    """Resolve type hints of a class."""

    for attribute in _get_attributes(cls):
        _resolve_object(getattr(cls, attribute), mapping)


def _resolve_mro(mro: Iterable[type], mapping: dict[str, Any]) -> None:
    """Resolve type hints of a method resolution order."""

    for cls in mro:
        _resolve_class(cls, mapping)


def resolve_type_hints(
    obj: Optional[type] = None, *, mapping: Optional[dict[str, Any]] = None
) -> Union[Callable[[Any], type], type]:
    """Decorator to resolve type hints on classes and functions."""

    if mapping is None:
        mapping = globals()
        mapping[obj.__name__] = obj

    def decorator(obj_: Any) -> type:
        try:
            mro = obj_.__mro__
        except AttributeError:
            _resolve_type_hints(obj_.__annotations__, mapping)
        else:
            _resolve_mro(mro, mapping)

        return obj_

    return decorator if obj is None else decorator(obj)


def resolve_all_type_hints(*objects: type) -> None:
    """Decorator to resolve type hints on classes and functions."""

    mapping = globals()
    mapping.update({obj.__name__: obj for obj in objects})

    for obj in objects:
        resolve_type_hints(obj, mapping=mapping)
