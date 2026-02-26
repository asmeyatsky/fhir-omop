"""
Whistle Engine Adapter

Architectural Intent:
- Infrastructure adapter implementing WhistleEnginePort
- Wraps Google's Whistle Data Transformation Language engine
- Phase 1: Python-based transformation interpreter for core mapping patterns
- Phase 2: will shell out to the actual Whistle CLI binary

Key Design Decision:
- Phase 1 uses a lightweight Python interpreter that handles the mapping
  templates we ship (Patient, Encounter, Condition, Observation)
- This avoids a Go/Java dependency for MVP while maintaining the same
  Whistle code format for forward compatibility
"""
from __future__ import annotations

import json
import re


class WhistleEngine:
    """
    Lightweight Whistle-compatible transformation engine.

    Executes field-level mapping rules encoded as Whistle-like directives.
    The mapping templates generate a simplified Whistle JSON-DSL that this
    engine interprets.
    """

    async def execute(
        self,
        whistle_code: str,
        input_resource: dict,
    ) -> dict | None:
        """Execute a Whistle mapping against a FHIR resource."""
        try:
            mapping_rules = json.loads(whistle_code)
        except json.JSONDecodeError:
            return None

        output: dict = {}
        for rule in mapping_rules.get("mappings", []):
            source_path = rule.get("source")
            target_field = rule.get("target")
            transform = rule.get("transform", "direct")
            params = rule.get("params", {})

            value = self._extract_value(input_resource, source_path)
            if value is None and not rule.get("allow_null", False):
                if rule.get("default") is not None:
                    value = rule["default"]
                else:
                    continue

            transformed = self._apply_transform(value, transform, params)
            if transformed is not None:
                output[target_field] = transformed

        return output if output else None

    async def validate_code(self, whistle_code: str) -> tuple[bool, list[str]]:
        errors: list[str] = []
        try:
            rules = json.loads(whistle_code)
            if "mappings" not in rules:
                errors.append("Missing 'mappings' key in Whistle code")
            else:
                for i, rule in enumerate(rules["mappings"]):
                    if "source" not in rule and "default" not in rule:
                        errors.append(f"Rule {i}: missing 'source' or 'default'")
                    if "target" not in rule:
                        errors.append(f"Rule {i}: missing 'target'")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        return len(errors) == 0, errors

    def _extract_value(self, resource: dict, path: str | None) -> object:
        """Extract a value from a nested dict using dot-notation path."""
        if path is None:
            return None
        parts = path.split(".")
        current: object = resource
        for part in parts:
            # Handle array indexing like "name[0]"
            match = re.match(r"(\w+)\[(\d+)\]", part)
            if match:
                key, idx = match.group(1), int(match.group(2))
                if isinstance(current, dict):
                    current = current.get(key)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def _apply_transform(
        self, value: object, transform: str, params: dict
    ) -> object:
        if transform == "direct":
            return value
        elif transform == "year_from_date":
            if isinstance(value, str) and len(value) >= 4:
                return int(value[:4])
        elif transform == "month_from_date":
            if isinstance(value, str) and len(value) >= 7:
                return int(value[5:7])
        elif transform == "day_from_date":
            if isinstance(value, str) and len(value) >= 10:
                return int(value[8:10])
        elif transform == "vocabulary_lookup":
            # Phase 1: pass through source code, vocabulary resolver handles in pipeline
            return value
        elif transform == "constant":
            return params.get("value")
        elif transform == "map":
            mapping = params.get("mapping", {})
            return mapping.get(str(value), params.get("default"))
        elif transform == "first_of_array":
            if isinstance(value, list) and value:
                return value[0]
        elif transform == "join":
            if isinstance(value, list):
                sep = params.get("separator", " ")
                return sep.join(str(v) for v in value)
        return value
