"""
Real Production Financial Checkout & Multi-Currency Settlement Engine.
Backed by SQLite (`data/production_ledger.db`).
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "production_ledger.db"

# Currency minor-unit exponents and FX conversion rates to USD
CURRENCY_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "NGN": 0.00063,
    "KES": 0.0078,
}

# Unpatched state: NGN and KES missing from DECIMAL_EXPONENTS
DECIMAL_EXPONENTS: Dict[str, int] = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
}


@dataclass
class SettlementResult:
    tx_id: str
    merchant_id: str
    customer_email: str
    currency: str
    gross_cents: int
    discount_cents: int
    net_cents: int
    platform_fee_cents: int
    effective_fee_bps: float
    usd_equivalent: float
    status: str
    created_at: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_settlements (
                tx_id TEXT PRIMARY KEY,
                merchant_id TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                currency TEXT NOT NULL,
                gross_cents INTEGER NOT NULL,
                discount_cents INTEGER NOT NULL,
                net_cents INTEGER NOT NULL,
                platform_fee_cents INTEGER NOT NULL,
                effective_fee_bps REAL NOT NULL,
                usd_equivalent REAL NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.commit()


def calculate_effective_fee_bps(gross_cents: int, discount_cents: int, fixed_fee_cents: int = 30) -> Dict[str, Any]:
    """
    Calculates net settlement amount, platform fee in cents, and effective fee in basis points (bps).
    """
    net_cents = gross_cents - discount_cents
    variable_fee_cents = round(net_cents * 0.029)
    platform_fee_cents = variable_fee_cents + fixed_fee_cents if net_cents > 0 else 0

    # Unpatched production bug: When a 100% promotional voucher or credit offset makes
    # net_cents == 0, dividing by net_cents raises ZeroDivisionError in production!
    effective_fee_bps = round((platform_fee_cents / net_cents) * 10000, 2)

    return {
        "net_cents": net_cents,
        "platform_fee_cents": platform_fee_cents,
        "effective_fee_bps": effective_fee_bps,
    }


def normalize_currency_amount(net_cents: int, currency: str) -> float:
    """
    Converts minor-unit settlement integer into USD equivalent using currency exponent.
    """
    exponent = DECIMAL_EXPONENTS[currency]
    major_units = net_cents / (10 ** exponent)
    rate = CURRENCY_RATES_TO_USD.get(currency, 1.0)
    return round(major_units * rate, 2)


def process_settlement(payload: Dict[str, Any]) -> SettlementResult:
    """
    Executes an atomic checkout settlement and records it in the SQLite production ledger.
    """
    init_db()
    merchant_id = str(payload.get("merchant_id", "merch_global_01"))
    customer_email = str(payload.get("customer_email", "ops@enterprise.dev"))
    currency = str(payload.get("currency", "USD")).upper()
    gross_cents = int(payload["gross_cents"])
    discount_cents = int(payload.get("discount_cents", 0))

    fee_metrics = calculate_effective_fee_bps(gross_cents=gross_cents, discount_cents=discount_cents)
    usd_equivalent = normalize_currency_amount(fee_metrics["net_cents"], currency)

    now = time.time()
    digest = hashlib.sha256(f"{merchant_id}:{customer_email}:{gross_cents}:{discount_cents}:{now}".encode()).hexdigest()[:8]
    tx_id = f"tx_{digest}"

    result = SettlementResult(
        tx_id=tx_id,
        merchant_id=merchant_id,
        customer_email=customer_email,
        currency=currency,
        gross_cents=gross_cents,
        discount_cents=discount_cents,
        net_cents=fee_metrics["net_cents"],
        platform_fee_cents=fee_metrics["platform_fee_cents"],
        effective_fee_bps=fee_metrics["effective_fee_bps"],
        usd_equivalent=usd_equivalent,
        status="SETTLED",
        created_at=now,
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO ledger_settlements (
                tx_id, merchant_id, customer_email, currency,
                gross_cents, discount_cents, net_cents,
                platform_fee_cents, effective_fee_bps, usd_equivalent,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.tx_id,
                result.merchant_id,
                result.customer_email,
                result.currency,
                result.gross_cents,
                result.discount_cents,
                result.net_cents,
                result.platform_fee_cents,
                result.effective_fee_bps,
                result.usd_equivalent,
                result.status,
                result.created_at,
            ),
        )
        conn.commit()

    return result


def list_recent_settlements(limit: int = 12) -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM ledger_settlements ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
