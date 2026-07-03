"""Unit tests for the tool argument schemas (no GCP / network required)."""
import pytest

from trading_assistant.schemas import (
    CalculatorArgs,
    ConvertArgs,
    ExchangeRateArgs,
    MarketPriceArgs,
    SpotOrderArgs,
    validate_args,
)


def test_spot_order_normalizes_case():
    model, err = validate_args(SpotOrderArgs, {
        "symbol": "btc", "side": "buy", "order_type": "limit",
        "quantity": "1.5", "price": "60000",
    })
    assert err is None
    assert (model.symbol, model.side, model.order_type) == ("BTC", "BUY", "LIMIT")


def test_spot_order_market_needs_no_price():
    model, err = validate_args(SpotOrderArgs, {
        "symbol": "eth", "side": "sell", "order_type": "market", "quantity": "2",
    })
    assert err is None and model.order_type == "MARKET"


@pytest.mark.parametrize("args,needle", [
    ({"symbol": "btc", "side": "hodl", "quantity": "1", "price": "1"}, "side"),
    ({"symbol": "btc", "side": "buy", "order_type": "limit", "quantity": "1"}, "price is required"),
    ({"symbol": "btc", "side": "buy", "order_type": "market", "quantity": "-3"}, "greater than zero"),
    ({"symbol": "btc", "side": "buy", "order_type": "market", "quantity": "abc"}, "numeric"),
])
def test_spot_order_rejects_bad_input(args, needle):
    model, err = validate_args(SpotOrderArgs, args)
    assert model is None and err["status"] == "error" and needle in err["message"]


def test_convert_rejects_same_and_usdt():
    _, same = validate_args(ConvertArgs, {"from_asset": "btc", "to_asset": "btc", "amount": "1"})
    assert same and "different" in same["message"]
    _, usdt = validate_args(ConvertArgs, {"from_asset": "usdt", "to_asset": "eth", "amount": "1"})
    assert usdt and "USDT" in usdt["message"]


def test_exchange_rate_distinct():
    _, err = validate_args(ExchangeRateArgs, {"from_asset": "btc", "to_asset": "btc"})
    assert err and "different" in err["message"]


def test_market_price_forbids_extra_fields():
    _, err = validate_args(MarketPriceArgs, {"symbol": "btc", "bogus": 1})
    assert err and "bogus" in err["message"]


@pytest.mark.parametrize("args,ok", [
    ({"a": "1", "b": "2", "operation": "add"}, True),
    ({"a": "x", "b": "2", "operation": "add"}, False),
    ({"a": "1", "b": "2", "operation": "power"}, False),
])
def test_calculator(args, ok):
    model, err = validate_args(CalculatorArgs, args)
    assert (err is None) == ok
