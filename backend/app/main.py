"""FoodBridge API.

Run (from the backend/ folder):
    uvicorn app.main:create_app --factory --reload
"""
import os
import sqlite3
from typing import Iterator, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from . import clock, db
from .schemas import ClaimOut, ClaimRequest, DonationCreate, DonationOut

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
SQLITE_MAX_INT = 2**63 - 1

DonationId = Path(ge=1, le=SQLITE_MAX_INT, description="Donation id")


def create_app(db_path: Optional[str] = None) -> FastAPI:
    db_path = db_path or os.environ.get("FOODBRIDGE_DB_PATH") or db.DEFAULT_DB_PATH
    origins = [
        o.strip()
        for o in os.environ.get("FOODBRIDGE_CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
        if o.strip()
    ]

    db.init_db(db_path)
    app = FastAPI(title="FoodBridge API", version="0.1.0")
    app.state.db_path = db_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )

    def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
        conn = db.connect(request.app.state.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/health", tags=["meta"])
    def health(conn: sqlite3.Connection = Depends(get_conn)) -> dict:
        conn.execute("SELECT 1")
        return {"status": "ok"}

    @app.post("/donations", response_model=DonationOut, status_code=201, tags=["donations"])
    def create_donation(payload: DonationCreate, conn: sqlite3.Connection = Depends(get_conn)):
        return db.create_donation(conn, payload.model_dump(), clock.utcnow())

    @app.get("/donations", response_model=list[DonationOut], tags=["donations"])
    def list_donations(
        status: Optional[Literal["available", "claimed", "expired"]] = Query(
            default=None, description="Filter by status"
        ),
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=1_000_000),
        conn: sqlite3.Connection = Depends(get_conn),
    ):
        return db.list_donations(conn, clock.utcnow(), status, limit, offset)

    @app.get("/donations/{donation_id}", response_model=DonationOut, tags=["donations"])
    def get_donation(donation_id: int = DonationId, conn: sqlite3.Connection = Depends(get_conn)):
        donation = db.get_donation(conn, donation_id, clock.utcnow())
        if donation is None:
            raise HTTPException(status_code=404, detail="Donation not found")
        return donation

    @app.post("/donations/{donation_id}/claim", response_model=ClaimOut, tags=["donations"])
    def claim_donation(
        payload: ClaimRequest,
        donation_id: int = DonationId,
        conn: sqlite3.Connection = Depends(get_conn),
    ):
        outcome, donation = db.claim_donation(
            conn, donation_id, payload.claimed_by, clock.utcnow()
        )
        if outcome == "not_found":
            raise HTTPException(status_code=404, detail="Donation not found")
        if outcome == "already_claimed":
            raise HTTPException(status_code=409, detail="This donation has already been claimed")
        if outcome == "expired":
            raise HTTPException(
                status_code=409, detail="This donation's pickup deadline has passed"
            )
        return donation

    return app
