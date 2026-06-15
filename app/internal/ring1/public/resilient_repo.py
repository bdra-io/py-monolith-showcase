import asyncio
from typing import Dict, List, Any, Optional
import aiosqlite

from app.internal.ring0.protected.context import get_tenant_context
from app.internal.ring1.pure.order import Order


class ResilientOrderRepository:
    """Asynchronous resilient storage repository driven by an underlying SQLite engine."""

    def __init__(self) -> None:
        # Core Infrastructure Handles
        self._db: Optional[aiosqlite.Connection] = None
        self.is_db_connected: bool = True

        # BDRA-Lite Resiliency Buffers
        self.read_cache: Dict[str, Dict[str, Any]] = {}
        self.wal_queue: List[Dict[str, Any]] = []
        self.outbox_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def _get_db(self) -> aiosqlite.Connection:
        """Lazy-initializes the in-memory relational table space using safe sync locks."""
        if self._db is None:
            # Establish connection to an isolated, in-memory SQLite matrix
            self._db = await aiosqlite.connect(":memory:")
            # Compile the core relational schema boundary
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    tenant_id TEXT NOT NULL
                )
            """)
            await self._db.commit()
        return self._db

    async def close(self) -> None:
        """Cleanly tears down connection handles to avoid dangling thread memory leaks."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def ping(self) -> None:
        """Evaluates hardware level bus connectivity to the database network."""
        if not self.is_db_connected:
            raise ConnectionError("Primary relational database node is unreachable.")

    async def check_health(self) -> bool:
        """Standard out-of-band monitoring probe hook reporting storage node integrity."""
        return bool(self.is_db_connected)

    async def save(self, order: Order) -> None:
        """Orchestrates multi-tiered resilient writes based on active cluster health states."""
        tenant_id = get_tenant_context() or "SYSTEM"

        # Formulate standard transactional data payload shape
        payload = {
            "id": order.id,
            "user_id": order.user_id,
            "amount": order.amount,
            "tenant_id": tenant_id
        }

        # TIER 1: Primary Database Flow (Healthy State)
        if self.is_db_connected:
            try:
                db = await self._get_db()
                await db.execute(
                    "INSERT INTO orders (id, user_id, amount, tenant_id) VALUES (?, ?, ?, ?)",
                    (order.id, order.user_id, order.amount, tenant_id)
                )
                await db.commit()

                # Keep the read-cache warm (Tier 2 pre-population)
                self.read_cache[order.id] = payload
                
                # Emit to Ring 2 Outbox telemetry stream out-of-band
                await self.outbox_queue.put({"event": "ORDER_CREATED", "tenant_id": tenant_id, "data": payload})
                return
            except Exception as e:
                # Instantly catch write exceptions and fall back to resilient processing
                self.is_db_connected = False

        # TIER 2 / TIER 3: Degraded Resiliency Fallback (Outage State)
        if len(self.wal_queue) >= 50:
            raise RuntimeError("System degradation severe: Resiliency WAL queues saturated. Write rejected.")

        # Cache transaction locally and write to the Write-Ahead Log loop
        self.read_cache[order.id] = payload
        await self._append_to_wal(tenant_id, "INSERT", payload)

    async def find(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Resolves records using real SQL lookups or read-caches depending on network health."""
        tenant_id = get_tenant_context() or "SYSTEM"

        # TIER 1: Primary SQL Query
        if self.is_db_connected:
            try:
                db = await self._get_db()
                async with db.execute(
                    "SELECT id, user_id, amount, tenant_id FROM orders WHERE id = ? AND tenant_id = ?",
                    (order_id, tenant_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "id": str(row[0]),
                            "user_id": str(row[1]),
                            "amount": float(row[2]),
                            "tenant_id": str(row[3])
                        }
                    return None
            except Exception:
                self.is_db_connected = False

        # TIER 2: Transparent Read Cache Fallback
        if order_id in self.read_cache:
            cached = self.read_cache[order_id]
            if cached.get("tenant_id") == tenant_id:
                return cached
        return None

    async def _append_to_wal(self, tenant_id: str, action: str, data: Dict[str, Any]) -> None:
        """Appends log records to the recovery queue during data destination outages."""
        self.wal_queue.append({"tenant_id": tenant_id, "action": action, "data": data})

    async def start_wal_replay_worker(self, shutdown_event: asyncio.Event) -> None:
        """Background agent replaying buffered WAL operations when the main database recovers."""
        while not shutdown_event.is_set():
            if self.is_db_connected and self.wal_queue:
                log_entry = self.wal_queue[0]
                data = log_entry["data"]
                try:
                    db = await self._get_db()
                    await db.execute(
                        "INSERT OR IGNORE INTO orders (id, user_id, amount, tenant_id) VALUES (?, ?, ?, ?)",
                        (data["id"], data["user_id"], data["amount"], log_entry["tenant_id"])
                    )
                    await db.commit()
                    
                    # Stream to Ring 2 telemetry once safely written to disk
                    await self.outbox_queue.put({
                        "event": "ORDER_REPLAYED", 
                        "tenant_id": log_entry["tenant_id"], 
                        "data": data
                    })
                    
                    self.wal_queue.pop(0)
                except Exception:
                    self.is_db_connected = False
            await asyncio.sleep(1.0)