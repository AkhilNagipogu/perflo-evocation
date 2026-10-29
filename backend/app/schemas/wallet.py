"""
Wallet and transaction schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    """Wallet balance response."""
    id: uuid.UUID
    balance_paise: int
    balance_display: str  # e.g., "₹60"
    has_been_funded: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletTopUpRequest(BaseModel):
    """Request to add funds to wallet."""
    amount_paise: int = Field(gt=0, description="Amount in paise to add")


class TransactionResponse(BaseModel):
    """Single transaction in the ledger."""
    id: uuid.UUID
    reference_id: str
    transaction_type: str
    status: str
    amount_paise: int
    balance_after_paise: int
    description: str
    rental_id: Optional[uuid.UUID] = None
    payment_order_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Paginated transaction list."""
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


class WalletSummaryResponse(BaseModel):
    """Monthly wallet summary."""
    balance_paise: int
    balance_display: str
    month_spending_paise: int
    month_funding_paise: int
    recent_transactions: list[TransactionResponse]
