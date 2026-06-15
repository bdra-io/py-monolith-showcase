import asyncio
import pytest
from typing import List, Dict, Any
from app.internal.ring1.public.resilient_repo import ResilientOrderRepository
from app.internal.ring1.pure.order import create_order
from app.internal.ring0.protected.context import set_tenant_context, clear_tenant_context

@pytest.mark.asyncio
async def test_mid_flight_database_blackout_and_recovery_chaos() -> None:
    """Simulates a sudden database connection drop mid-transaction blast, 
    verifying automated fallback routing, concurrent isolation, and background recovery replay.
    """
    repo = ResilientOrderRepository()
    
    # 1. Establish initial healthy state and seed an order
    token_alpha = set_tenant_context("tenant_alpha")
    try:
        order_healthy = create_order("ord_chaos_0", "user_1", 100.0)
        await repo.save(order_healthy)
        assert repo.is_db_connected is True
        assert len(repo.wal_queue) == 0
    finally:
        clear_tenant_context(token_alpha)

    # 2. TRIGGER CHAOS: Programmatically cut the database connection strings
    repo.is_db_connected = False
    
    # Define a concurrent blast of incoming orders from multiple isolated tenants
    chaos_payloads: List[Dict[str, Any]] = [
        {"tenant": "tenant_alpha", "id": "ord_chaos_1", "user": "user_1", "amt": 50.0},
        {"tenant": "tenant_beta",  "id": "ord_chaos_2", "user": "user_2", "amt": 75.0},
        {"tenant": "tenant_gamma", "id": "ord_chaos_3", "user": "user_3", "amt": 120.0},
        {"tenant": "tenant_alpha", "id": "ord_chaos_4", "user": "user_1", "amt": 200.0},
    ]

    async def simulate_isolated_tenant_write(payload: Dict[str, Any]) -> None:
        """Helper to bind context variables per concurrent task iteration."""
        token = set_tenant_context(payload["tenant"])
        try:
            order = create_order(payload["id"], payload["user"], payload["amt"])
            await repo.save(order)
        finally:
            clear_tenant_context(token)

    # 3. Fire the concurrent transaction payload burst
    await asyncio.gather(*(simulate_isolated_tenant_write(p) for p in chaos_payloads))

    # 4. ASSERT DEGRADED STATE INTEGRITY: All 4 concurrent orders must safely route to WAL
    assert len(repo.wal_queue) == 4
    
    token_beta = set_tenant_context("tenant_beta")
    try:
        cached_order = await repo.find("ord_chaos_2")
        assert cached_order is not None
        assert float(cached_order["amount"]) == 75.0
    finally:
        clear_tenant_context(token_beta)

    # 5. HEAL THE INFRASTRUCTURE: Bring the database back online
    repo.is_db_connected = True

    # 6. RECOVERY ORCHESTRATION: Spin up the replayer worker
    shutdown_event = asyncio.Event()
    replayer_task = asyncio.create_task(repo.start_wal_replay_worker(shutdown_event))

    # UPDATED: Dynamic Polling Loop. Check every 100ms for up to 5.0 seconds max.
    for _ in range(50):
        if len(repo.wal_queue) == 0:
            break
        await asyncio.sleep(0.1)

    # Stop the worker task cleanly
    shutdown_event.set()
    await replayer_task

    # 7. FINAL VERIFICATION: WAL must be completely drained
    assert len(repo.wal_queue) == 0
    
    token_gamma = set_tenant_context("tenant_gamma")
    try:
        persisted_order = await repo.find("ord_chaos_3")
        assert persisted_order is not None
        assert persisted_order["tenant_id"] == "tenant_gamma"
    finally:
        clear_tenant_context(token_gamma)
        await repo.close()