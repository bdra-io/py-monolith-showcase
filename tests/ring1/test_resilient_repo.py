import asyncio
import pytest
from app.internal.ring1.public.resilient_repo import ResilientOrderRepository
from app.internal.ring1.pure.order import create_order
from app.internal.ring0.protected.context import set_tenant_context, clear_tenant_context


@pytest.mark.asyncio
async def test_resilient_repo_healthy_execution_flow() -> None:
    """Verifies that transactions commit smoothly into SQL storage without generating WAL logs under healthy conditions."""
    repo = ResilientOrderRepository()
    
    # 1. Establish the secure isolation boundary token for the test execution track
    token = set_tenant_context("test_tenant_alpha")
    
    try:
        # 2. Utilize the domain factory to create a valid Order entity
        order = create_order(order_id="test_ord_healthy", user_id="usr_comp_1", amount=150.00)
        
        # 3. Write straight to the live database abstraction layer
        await repo.save(order)
        
        # 4. Assert data presence inside primary relational space
        found = await repo.find("test_ord_healthy")
        assert found is not None
        assert found["user_id"] == "usr_comp_1"
        assert float(found["amount"]) == 150.00
        
        # 5. Verify no fallbacks were triggered
        assert len(repo.wal_queue) == 0
        assert repo.outbox_queue.qsize() == 1
    finally:
        # 6. Always unwind state context variables and drop database links
        clear_tenant_context(token)
        await repo.close()


@pytest.mark.asyncio
async def test_resilient_repo_degraded_outage_fallback_and_replay() -> None:
    """Tests that infrastructure outages trigger memory buffers and recovery replayer background tasks."""
    repo = ResilientOrderRepository()
    token = set_tenant_context("test_tenant_beta")
    
    try:
        # 1. Force a degraded operational status state
        repo.is_db_connected = False
        
        order = create_order(order_id="test_ord_degraded", user_id="usr_comp_2", amount=450.75)
        await repo.save(order)
        
        # 2. Assert transaction was rerouted to the resiliency Write-Ahead Log loop
        assert len(repo.wal_queue) == 1
        assert repo.wal_queue[0]["data"]["id"] == "test_ord_degraded"
        
        # 3. Heal the infrastructure lines programmatically
        repo.is_db_connected = True
        
        # 4. Spin up the background recovery agent loop temporarily
        shutdown_event = asyncio.Event()
        worker_task = asyncio.create_task(repo.start_wal_replay_worker(shutdown_event))
        
        # Give the background worker tick 1.1 seconds to process the queue frame
        await asyncio.sleep(1.1)
        
        # Signal clean loop termination closure to the task
        shutdown_event.set()
        await worker_task
        
        # 5. Verify the WAL array drained completely and records are flushed to the real DB
        assert len(repo.wal_queue) == 0
        
        found = await repo.find("test_ord_degraded")
        assert found is not None
        assert float(found["amount"]) == 450.75
    finally:
        clear_tenant_context(token)
        await repo.close()