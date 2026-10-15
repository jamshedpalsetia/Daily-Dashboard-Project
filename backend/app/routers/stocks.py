from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WatchlistItem
from app.providers import stocks_yfinance
from app.schemas import WatchlistItemIn, WatchlistItemUpdate
from app.services import widgets

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/movers")
def read_movers(db: Session = Depends(get_db)) -> dict:
    try:
        return widgets.movers_payload(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"movers unavailable: {exc}") from exc


@router.get("/watchlist")
def read_watchlist(db: Session = Depends(get_db)) -> dict:
    try:
        return widgets.watchlist_payload(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"quotes unavailable: {exc}") from exc


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
def add_watchlist_item(payload: WatchlistItemIn, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(WatchlistItem).where(WatchlistItem.symbol == payload.symbol))
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"{payload.symbol} is already tracked")

    if not stocks_yfinance.validate_symbol(payload.symbol):
        raise HTTPException(
            status_code=422, detail=f"no market data found for {payload.symbol}"
        )

    item = WatchlistItem(
        symbol=payload.symbol, shares=payload.shares, cost_basis=payload.cost_basis
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "symbol": item.symbol}


@router.patch("/watchlist/{item_id}")
def update_watchlist_item(
    item_id: int, payload: WatchlistItemUpdate, db: Session = Depends(get_db)
) -> dict:
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    return {"id": item.id, "symbol": item.symbol}


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(item_id: int, db: Session = Depends(get_db)) -> Response:
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
