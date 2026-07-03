"""Strict Pydantic argument models for the agent tools.

ADK derives a JSON schema for each tool from its function signature, but that
only enforces *types*. These models add *semantic* validation (enums, positive
amounts, "from != to", decimal-parseable strings) so bad arguments are rejected
deterministically with a guided error message the LLM can recover from, instead
of blowing up deep inside a service call.

Each tool calls ``validate_args(Model, {...})`` at its entry point and returns
``err`` verbatim to the model when validation fails.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple, Type

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _to_upper(v: Optional[str]) -> Optional[str]:
    return v.strip().upper() if isinstance(v, str) else v


_CALC_OPS = frozenset({
    "multiply", "multiplication", "*", "times",
    "divide", "division", "/", "divided by",
    "add", "addition", "+", "plus", "sum",
    "subtract", "subtraction", "-", "minus",
})


def _positive_decimal(name: str, value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} must be a numeric string, got {value!r}")
    if d <= 0:
        raise ValueError(f"{name} must be greater than zero, got {value!r}")
    return str(value)


class SpotOrderArgs(BaseModel):
    """Arguments for ``execute_spot_order``."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    side: str
    order_type: str = "LIMIT"
    quantity: Optional[str] = None
    price: Optional[str] = None

    _up_symbol = field_validator("symbol", mode="before")(lambda v: _to_upper(v))

    @field_validator("side", mode="before")
    @classmethod
    def _valid_side(cls, v: str) -> str:
        v = _to_upper(v)
        if v not in ("BUY", "SELL"):
            raise ValueError('side must be "BUY" or "SELL"')
        return v

    @field_validator("order_type", mode="before")
    @classmethod
    def _valid_order_type(cls, v: str) -> str:
        v = _to_upper(v) or "LIMIT"
        if v not in ("LIMIT", "MARKET"):
            raise ValueError('order_type must be "LIMIT" or "MARKET"')
        return v

    @field_validator("quantity")
    @classmethod
    def _valid_quantity(cls, v: Optional[str]) -> Optional[str]:
        return _positive_decimal("quantity", v)

    @field_validator("price")
    @classmethod
    def _valid_price(cls, v: Optional[str]) -> Optional[str]:
        return _positive_decimal("price", v)

    @model_validator(mode="after")
    def _limit_needs_price(self) -> "SpotOrderArgs":
        if self.order_type == "LIMIT" and not self.price:
            raise ValueError("price is required for LIMIT orders")
        return self


class ConvertArgs(BaseModel):
    """Arguments for ``execute_convert_operation``."""

    model_config = ConfigDict(extra="forbid")

    from_asset: str
    to_asset: str
    amount: Optional[str] = None

    _up_from = field_validator("from_asset", mode="before")(lambda v: _to_upper(v))
    _up_to = field_validator("to_asset", mode="before")(lambda v: _to_upper(v))

    @field_validator("amount")
    @classmethod
    def _valid_amount(cls, v: Optional[str]) -> Optional[str]:
        return _positive_decimal("amount", v)

    @model_validator(mode="after")
    def _distinct_non_usdt(self) -> "ConvertArgs":
        if self.from_asset == self.to_asset:
            raise ValueError("from_asset and to_asset must be different")
        if "USDT" in (self.from_asset, self.to_asset):
            raise ValueError(
                "USDT trades must use the spot tool; convert is crypto-to-crypto only"
            )
        return self


class MarketPriceArgs(BaseModel):
    """Arguments for ``get_price``."""

    model_config = ConfigDict(extra="forbid")

    symbol: str

    _up_symbol = field_validator("symbol", mode="before")(lambda v: _to_upper(v))


class ExchangeRateArgs(BaseModel):
    """Arguments for ``get_exchange_rate``."""

    model_config = ConfigDict(extra="forbid")

    from_asset: str
    to_asset: str

    _up_from = field_validator("from_asset", mode="before")(lambda v: _to_upper(v))
    _up_to = field_validator("to_asset", mode="before")(lambda v: _to_upper(v))

    @model_validator(mode="after")
    def _distinct(self) -> "ExchangeRateArgs":
        if self.from_asset == self.to_asset:
            raise ValueError("from_asset and to_asset must be different")
        return self


class CalculatorArgs(BaseModel):
    """Arguments for ``calculate_precise``."""

    model_config = ConfigDict(extra="forbid")

    a: str
    b: str
    operation: str

    @field_validator("a", "b")
    @classmethod
    def _numeric(cls, v: str) -> str:
        try:
            Decimal(str(v))
        except (InvalidOperation, ValueError):
            raise ValueError(f"operands must be numeric strings, got {v!r}")
        return v

    @field_validator("operation")
    @classmethod
    def _known_op(cls, v: str) -> str:
        if str(v).lower() not in _CALC_OPS:
            raise ValueError(
                "operation must be one of multiply/divide/add/subtract (or *,/,+,-)"
            )
        return v


def validate_args(
    model: Type[BaseModel], args: Dict[str, Any]
) -> Tuple[Optional[BaseModel], Optional[Dict[str, Any]]]:
    """Validate ``args`` against ``model``.

    Returns ``(instance, None)`` on success or ``(None, error_dict)`` on failure,
    where ``error_dict`` is a guided, LLM-friendly error payload.
    """
    try:
        return model(**args), None
    except Exception as exc:  # pydantic.ValidationError or TypeError
        details = []
        errors = getattr(exc, "errors", None)
        if callable(errors):
            for e in exc.errors():
                loc = ".".join(str(x) for x in e.get("loc", ())) or "arguments"
                details.append(f"{loc}: {e.get('msg')}")
        message = "; ".join(details) or str(exc)
        return None, {
            "status": "error",
            "message": f"Invalid arguments for {model.__name__}: {message}",
        }
