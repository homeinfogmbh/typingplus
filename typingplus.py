"""Enhanced type hinting hacks."""

from typing import _UnionGenericAlias
from typing import Any
from typing import ForwardRef
from typing import Iterable


__all__ = ['resolve_type_hints']


def _resolve_union_generic_alias(
        uga: _UnionGenericAlias, mapping: dict[str, Any]
    ) -> Any:
    """Resolve the type."""

    return _UnionGenericAlias(
        uga.__origin__,
        tuple(_resolve_type_hint(a, mapping) for a in uga.__args__),
        inst=uga._inst,     # pylint: disable=W0212
        name=uga._name,     # pylint: disable=W0212
        _typevar_types=uga._typevar_types,  # pylint: disable=W0212
        _paramspec_tvars=uga._paramspec_tvars   # pylint: disable=W0212
    )


def _resolve_type_hint(value: Any, mapping: dict[str, Any]) -> Any:
    """Resolves a type hint."""

    if isinstance(value, str):
        return mapping.get(value, value)

    if isinstance(value, ForwardRef):
        return _resolve_type_hint(value.__forward_arg__, mapping)

    if type(value) is _UnionGenericAlias:   # pylint: disable=C0123
        return _resolve_union_generic_alias(value, mapping)

    return value


def _resolve_type_hints(
        annotations: dict[str, Any], mapping: dict[str, Any]
    ) -> None:
    """Resolves type hints of the given annotations dict."""

    for key, value in dict(annotations).items():
        annotations[key] = _resolve_type_hint(value, mapping)


def _resolve_mro(mro: Iterable[type], mapping: dict[str, Any]) -> None:
    """Resolve type hints of a method resolution order."""

    for cls in mro:
        for attribute in cls.__dict__:
            try:
                annotations = getattr(cls, attribute).__annotations__
            except AttributeError:
                continue

            _resolve_type_hints(annotations, mapping)


def resolve_type_hints(obj: type) -> type:
    """Decorator to resolves type hints on classes and functions."""

    mapping = globals()
    mapping[obj.__name__] = obj

    try:
        mro = obj.__mro__
    except AttributeError:
        _resolve_type_hints(obj.__annotations__, mapping)
    else:
        _resolve_mro(mro, mapping)

    return obj
