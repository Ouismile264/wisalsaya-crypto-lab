from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd


BANGKOK = ZoneInfo("Asia/Bangkok")


class Storage:
    """Small SQLite repository used by the Streamlit UI.

    SQLite makes data durable across browser refreshes, tab closes and normal app
    process restarts. Community Cloud may replace the whole container during a
    redeploy, so CSV backup/import remains available in the UI.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _create_schema(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    coin TEXT NOT NULL,
                    side TEXT NOT NULL DEFAULT 'LONG',
                    entry REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    risk_baht REAL NOT NULL,
                    position_baht REAL NOT NULL,
                    current_price REAL NOT NULL,
                    exit_price REAL,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    unrealized_pnl REAL NOT NULL DEFAULT 0,
                    realized_pnl REAL NOT NULL DEFAULT 0,
                    reason TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    journal_date TEXT NOT NULL,
                    trade_id INTEGER,
                    coin TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    result_baht REAL NOT NULL DEFAULT 0,
                    emotion TEXT NOT NULL DEFAULT 'ปกติ',
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(trade_id) REFERENCES paper_trades(id) ON DELETE SET NULL
                );
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(BANGKOK).isoformat(timespec="seconds")

    def create_trade(self, trade: dict[str, Any]) -> int:
        now = self.now()
        with self.connect() as db:
            cursor = db.execute(
                """
                INSERT INTO paper_trades (
                    created_at, updated_at, coin, entry, stop_loss, take_profit,
                    risk_baht, position_baht, current_price, status, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
                """,
                (
                    now, now, trade["coin"], trade["entry"], trade["stop_loss"],
                    trade["take_profit"], trade["risk_baht"], trade["position_baht"],
                    trade["current_price"], trade.get("reason", ""),
                ),
            )
            return int(cursor.lastrowid)

    def list_trades(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM paper_trades ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def get_trade(self, trade_id: int) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone()
        return dict(row) if row else None

    def update_market_price(self, trade_id: int, current_price: float) -> None:
        trade = self.get_trade(trade_id)
        if not trade or trade["status"] != "OPEN":
            return
        status = "OPEN"
        exit_price = None
        if current_price <= trade["stop_loss"]:
            status, exit_price = "CLOSED_STOP", trade["stop_loss"]
        elif current_price >= trade["take_profit"]:
            status, exit_price = "CLOSED_TARGET", trade["take_profit"]
        mark = exit_price if exit_price is not None else current_price
        pnl = (mark - trade["entry"]) / trade["entry"] * trade["position_baht"]
        now = self.now()
        with self.connect() as db:
            if status == "OPEN":
                db.execute(
                    "UPDATE paper_trades SET current_price=?, unrealized_pnl=?, updated_at=? WHERE id=?",
                    (current_price, pnl, now, trade_id),
                )
            else:
                db.execute(
                    """UPDATE paper_trades SET current_price=?, exit_price=?, status=?,
                    unrealized_pnl=0, realized_pnl=?, updated_at=?, closed_at=? WHERE id=?""",
                    (current_price, exit_price, status, pnl, now, now, trade_id),
                )

    def close_trade(self, trade_id: int, exit_price: float) -> None:
        trade = self.get_trade(trade_id)
        if not trade or trade["status"] != "OPEN":
            return
        pnl = (exit_price - trade["entry"]) / trade["entry"] * trade["position_baht"]
        now = self.now()
        with self.connect() as db:
            db.execute(
                """UPDATE paper_trades SET current_price=?, exit_price=?, status='CLOSED_MANUAL',
                unrealized_pnl=0, realized_pnl=?, updated_at=?, closed_at=? WHERE id=?""",
                (exit_price, exit_price, pnl, now, now, trade_id),
            )

    def create_journal(self, entry: dict[str, Any]) -> int:
        with self.connect() as db:
            cursor = db.execute(
                """INSERT INTO journal_entries
                (created_at, journal_date, trade_id, coin, decision, result_baht, emotion, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.now(), entry["journal_date"], entry.get("trade_id"), entry["coin"],
                    entry["decision"], entry.get("result_baht", 0), entry["emotion"],
                    entry.get("notes", ""),
                ),
            )
            return int(cursor.lastrowid)

    def list_journal(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT j.*, t.status AS trade_status FROM journal_entries j
                LEFT JOIN paper_trades t ON t.id = j.trade_id ORDER BY j.id DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def migrate_session(self, trades: Iterable[dict], journal: Iterable[dict]) -> tuple[int, int]:
        trade_count = journal_count = 0
        for old in trades:
            try:
                self.create_trade({
                    "coin": old["coin"], "entry": float(old["entry"]),
                    "stop_loss": float(old.get("stop", old.get("stop_loss"))),
                    "take_profit": float(old.get("target", old.get("take_profit"))),
                    "risk_baht": float(old.get("risk", old.get("risk_baht", 0))),
                    "position_baht": float(old.get("position", old.get("position_baht", 0))),
                    "current_price": float(old.get("current", old["entry"])),
                    "reason": old.get("reason", "Migrated from session"),
                })
                trade_count += 1
            except (KeyError, TypeError, ValueError):
                continue
        for old in journal:
            try:
                self.create_journal({
                    "journal_date": str(old.get("วันที่", old.get("journal_date"))),
                    "coin": old.get("เหรียญ", old.get("coin", "ไม่ระบุ")),
                    "decision": old.get("Decision", old.get("decision", "WAIT")),
                    "result_baht": float(old.get("ผลลัพธ์", old.get("result_baht", 0))),
                    "emotion": old.get("อารมณ์", old.get("emotion", "ปกติ")),
                    "notes": old.get("บทเรียน", old.get("notes", "")),
                })
                journal_count += 1
            except (TypeError, ValueError):
                continue
        return trade_count, journal_count

    def import_trades_csv(self, frame: pd.DataFrame) -> int:
        aliases = {"stop": "stop_loss", "target": "take_profit", "risk": "risk_baht", "position": "position_baht", "current": "current_price"}
        frame = frame.rename(columns=aliases)
        count = 0
        for row in frame.to_dict("records"):
            try:
                self.create_trade(row)
                count += 1
            except (KeyError, TypeError, ValueError):
                continue
        return count

    def import_journal_csv(self, frame: pd.DataFrame) -> int:
        aliases = {"วันที่": "journal_date", "เหรียญ": "coin", "Decision": "decision", "ผลลัพธ์": "result_baht", "อารมณ์": "emotion", "บทเรียน": "notes"}
        frame = frame.rename(columns=aliases)
        count = 0
        for row in frame.to_dict("records"):
            try:
                self.create_journal(row)
                count += 1
            except (KeyError, TypeError, ValueError):
                continue
        return count
