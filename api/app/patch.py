"""Patch the openapi schema for list form body params to add an encoding field which
forces swaggerUI to "explode" the params it sends

This is adapted from https://github.com/tiangolo/fastapi/issues/3532#issuecomment-1318097787
"""

from enum import Enum
from typing import Any, Dict, Optional, Type, Union

import fastapi.openapi.utils
from fastapi.openapi.constants import REF_PREFIX
from pydantic import BaseModel
from pydantic.fields import ModelField
from pydantic.schema import field_schema

orig_get_request_body = fastapi.openapi.utils.get_openapi_operation_request_body


def get_request_body_with_explode(
    *,
    body_field: Optional[ModelField],
    model_name_map: Dict[Union[Type[BaseModel], Type[Enum]], str],
) -> Optional[Dict[str, Any]]:
    """Monkeypatch fastapi's function with this one to enable swaggerui to correctly
    send "exploded" data

    e.g.:
    fastapi.openapi.utils.get_openapi_operation_request_body = get_request_body_with_explode
    """

    original = orig_get_request_body(
        body_field=body_field, model_name_map=model_name_map
    )
    if not original:
        return original

    content = original.get("content", {})
    if form_patch := (
        content.get("application/x-www-form-urlencoded")
        or content.get("multipart/form-data")
    ):
        _, schemas, _ = field_schema(
            body_field, model_name_map=model_name_map, ref_prefix=REF_PREFIX
        )
        # from the body, identify all the "array" properties
        array_props = []
        for schema in schemas.values():  # type: Dict[str, Any]
            for prop, prop_schema in schema.get("properties", {}).items():
                if prop_schema.get("type") == "array":
                    array_props.append(prop)

        form_patch["encoding"] = {
            prop: {"style": "form"} for prop in array_props
        }  # could include "explode": True but not necessary in swagger-ui

    return original
