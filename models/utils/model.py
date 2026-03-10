# encoding=utf-8
import logging

from typing import Type, List, Any, get_origin, get_args, Union, Optional
import typing as t
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from typing_extensions import Annotated, get_args, get_origin

logger = logging.getLogger(__name__)


Json = t.Any


@dataclass
class Patch:
    path: str
    action: str         # drop_field | drop_item | drop_root | drop_value
    original: Json
    reason: str


@dataclass
class CleanResult:
    cleaned: Json | None        # None means root dropped
    patches: list[Patch]


class _Drop:
    pass


_DROP = _Drop()


def clean_json_for_model(model_cls: type[BaseModel], data: Json) -> CleanResult:
    patches: list[Patch] = []
    cleaned = _clean_against_type(model_cls, data, model_cls.__name__, patches, root_model=model_cls)

    if cleaned is _DROP:
        patches.append(Patch(model_cls.__name__, "drop_root", data, "root dropped by rule"))
        return CleanResult(cleaned=None, patches=patches)

    return CleanResult(cleaned=cleaned, patches=patches)


# ---------------- internals ----------------

def _unwrap_annotated(tp: object) -> object:
    if get_origin(tp) is Annotated:
        return get_args(tp)[0]
    return tp


def _is_enum(tp: object) -> bool:
    try:
        return isinstance(tp, type) and issubclass(tp, Enum)
    except TypeError:
        return False


def _enum_parse(enum_cls: type[Enum], v: t.Any) -> Enum | _Drop:
    if isinstance(v, enum_cls):
        return v
    try:
        return enum_cls(v)  # by value
    except Exception:
        pass
    if isinstance(v, str):
        try:
            return enum_cls[v]  # by name
        except Exception:
            pass
    return _DROP


def _is_optional(tp: object) -> bool:
    tp = _unwrap_annotated(tp)
    return get_origin(tp) is t.Union and type(None) in get_args(tp)


def _required_field_names(model_cls: type[BaseModel]) -> set[str]:
    req = set()
    for n, f in model_cls.model_fields.items():
        # v2: required if no default and not default_factory
        if f.is_required():
            req.add(n)
    return req


def _model_has_any_enum(model_cls: type[BaseModel]) -> bool:
    ann = getattr(model_cls, "__annotations__", {}) or {}
    return any(_contains_enum(tp) for tp in ann.values())


def _contains_enum(tp: object) -> bool:
    tp = _unwrap_annotated(tp)
    if _is_enum(tp):
        return True
    origin = get_origin(tp)
    if origin is None:
        return False
    return any(_contains_enum(a) for a in get_args(tp))


def _clean_against_type(
    tp: object,
    value: Json,
    path: str,
    patches: list[Patch],
    *,
    root_model: type[BaseModel],
) -> Json | _Drop:
    tp = _unwrap_annotated(tp)
    origin = get_origin(tp)
    args = get_args(tp)

    # BaseModel
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        if not isinstance(value, dict):
            patches.append(Patch(path, "drop_value", value, f"expected object for {tp.__name__}"))
            return _DROP
        return _clean_model(tp, value, path, patches, root_model=root_model)

    # Enum scalar: invalid => DROP FIELD (caller decides)
    if _is_enum(tp):
        ev = _enum_parse(t.cast(type[Enum], tp), value)
        if ev is _DROP:
            patches.append(Patch(path, "drop_field", value, f"invalid enum {tp.__name__}"))
            return _DROP
        return ev

    # Union/Optional
    if origin is t.Union:
        if value is None and type(None) in args:
            return None
        for sub in args:
            if sub is type(None):
                continue
            cleaned = _clean_against_type(sub, value, path, patches, root_model=root_model)
            if cleaned is not _DROP:
                return cleaned
        patches.append(Patch(path, "drop_value", value, "no union branch matched"))
        return _DROP

    # list[T]
    if origin in (list, t.List):
        if not isinstance(value, list):
            patches.append(Patch(path, "drop_value", value, "expected list"))
            return _DROP

        item_tp = args[0] if args else t.Any
        item_base = _unwrap_annotated(item_tp)

        # If list items are BaseModel: we may drop item if enum invalid OR required field missing
        if isinstance(item_base, type) and issubclass(item_base, BaseModel):
            req = _required_field_names(item_base)
            out = []
            for i, item in enumerate(value):
                item_path = f"{path}[{i}]"
                if not isinstance(item, dict):
                    patches.append(Patch(item_path, "drop_item", item, "expected object item"))
                    continue

                # required fields present? (by name or alias)
                missing_req = []
                for fn in req:
                    f = item_base.model_fields[fn]
                    keys = {fn}
                    if f.alias:
                        keys.add(f.alias)
                    if not any(k in item for k in keys):
                        missing_req.append(fn)

                if missing_req:
                    patches.append(Patch(item_path, "drop_item", item, f"missing required fields: {missing_req}"))
                    continue

                # clean the item with local patches
                local_patches: list[Patch] = []
                cleaned_item = _clean_against_type(item_tp, item, item_path, local_patches, root_model=root_model)

                # If any enum field was dropped => drop the whole item
                enum_dropped = any(p.action == "drop_field" and "invalid enum" in p.reason for p in local_patches)
                if cleaned_item is _DROP or enum_dropped:
                    patches.append(Patch(item_path, "drop_item", item, "enum invalid in item -> drop item"))
                    patches.extend(local_patches)
                    continue

                patches.extend(local_patches)
                out.append(cleaned_item)

            return out

        # list of non-model: clean element-wise; drop invalid element
        out = []
        for i, item in enumerate(value):
            cleaned_item = _clean_against_type(item_tp, item, f"{path}[{i}]", patches, root_model=root_model)
            if cleaned_item is _DROP:
                patches.append(Patch(f"{path}[{i}]", "drop_item", item, "invalid element"))
                continue
            out.append(cleaned_item)
        return out

    # dict[K,V]
    if origin in (dict, t.Dict):
        if not isinstance(value, dict):
            patches.append(Patch(path, "drop_value", value, "expected dict"))
            return _DROP
        key_tp = args[0] if len(args) > 0 else t.Any
        val_tp = args[1] if len(args) > 1 else t.Any
        out = {}
        for k, v in value.items():
            ck = _clean_against_type(key_tp, k, f"{path}.<key>", patches, root_model=root_model)
            cv = _clean_against_type(val_tp, v, f"{path}[{k!r}]", patches, root_model=root_model)
            if ck is _DROP or cv is _DROP:
                patches.append(Patch(f"{path}[{k!r}]", "drop_item", {k: v}, "invalid dict entry"))
                continue
            out[ck] = cv
        return out

    # primitive: keep
    return value


def _clean_model(
    model_cls: type[BaseModel],
    obj: dict,
    path: str,
    patches: list[Patch],
    *,
    root_model: type[BaseModel],
) -> dict | _Drop:
    out: dict[str, Json] = {}

    # clean known fields
    for fname, field in model_cls.model_fields.items():
        alias = field.alias or fname
        raw_marker = object()

        raw = obj.get(alias, raw_marker)
        if raw is raw_marker:
            raw = obj.get(fname, raw_marker)

        if raw is raw_marker:
            continue

        cleaned = _clean_against_type(field.annotation, raw, f"{path}.{fname}", patches, root_model=root_model)
        if cleaned is _DROP:
            continue
        out[alias] = cleaned

    # After cleaning, enforce: if this is ROOT model, and any required field missing -> DROP ROOT
    if model_cls is root_model:
        for fname, field in model_cls.model_fields.items():
            if not field.is_required():
                continue
            alias = field.alias or fname
            if alias not in out and fname not in out:
                patches.append(Patch(f"{path}.{fname}", "drop_root", obj, f"missing required field: {fname}"))
                return _DROP

    return out




