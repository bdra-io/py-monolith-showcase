import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncIterator, Dict, Any

# Ring 0: Core Foundation Structural Infrastructure
from app.internal.ring0.public.postgres import PostgresIdentityProvider

# Ring 1: Transactional Core Domain Infrastructure & Sub-systems
from app.internal.ring1.public import http_adapter, order_dashboard
from app.internal.ring1.public.resilient_repo import ResilientOrderRepository
from app.internal.ring1.health.health import DomainMonitor
from app.internal.ring1.billing.public import http_adapter as billing_adapter

# Ring 2: Operational Intelligence Infrastructure (Asynchronous Threat Engine)
from app.internal.ring2.public.workers import OutboxStreamingWorker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Orchestration Composition Root governing system lifecycle and structured concurrency."""
    # 1. Instantiate Core Architectural Engines
    identity_engine = PostgresIdentityProvider()
    repo = ResilientOrderRepository()
    monitor = DomainMonitor(repo)
    worker = OutboxStreamingWorker(repo)
    
    # Bind initialized repository handles to HTTP delivery routers
    http_adapter._global_repo = repo
    
    # Initialize a global cancellation signal for background tasks
    shutdown_event = asyncio.Event()
    
    # 2. Define the Supervised Structured Worker Pool
    async def run_worker_pool() -> None:
        print("🏗️ [CONCURRENCY] Initializing structured background worker group...")
        try:
            async with asyncio.TaskGroup() as tg:
                # All background tasks are structurally tied to this block's execution lifecycle
                tg.create_task(repo.start_wal_replay_worker(shutdown_event))
                tg.create_task(monitor.start_monitoring_loop(shutdown_event))
                tg.create_task(worker.start_streaming_loop(shutdown_event))
                
        except ExceptionGroup as eg:
            print("\n🚨 [CRITICAL ALERT] Background worker group collapsed due to unhandled exceptions!")
            for exc in eg.exceptions:
                print(f"  ↳ Exception Tracked: {type(exc).__name__}: {exc}")
            print("🛑 System runtime compromised. Initiating emergency fail-safe procedures.\n")

    # 3. Launch supervisor out-of-band to prevent blocking HTTP server startup
    supervisor_task = asyncio.create_task(run_worker_pool())
    
    print("🚀 [BDRA-LITE] Python Modular Monolith fully assembled and operational.")
    
    try:
        yield  # 💻 The ASGI HTTP Gateway is online and actively handling API traffic here
    finally:
        # 4. Orderly Graceful Tear-down Sequence
        print("🧼 [SHUTDOWN] Signal captured. Gracefully flushing worker streams...")
        shutdown_event.set()
        
        # CLOSE THE SQLITE CONNECTION HANDLES CLEANLY HERE:
        await repo.close()
        
        # Allot workers a explicit time window to flush logs and queues cleanly
        try:
            await asyncio.wait_for(supervisor_task, timeout=3.0)
            print("✨ [SHUTDOWN] All background processes terminated cleanly.")
        except asyncio.TimeoutError:
            print("⚠️ [SHUTDOWN] Some background tasks failed to exit inside the timeout window; forcing cleanup.")


# Initialize the primary application node bound to our lifespan supervisor
app = FastAPI(
    title="BDRA-Lite Modular Monolith Showcase",
    version="1.0.0",
    lifespan=lifespan
)

# Mount Layer 3 Public Delivery API Routers
app.include_router(http_adapter.router)
app.include_router(order_dashboard.router)
app.include_router(billing_adapter.router)


@app.get("/")
async def root_landing_page() -> Dict[str, Any]:
    """Provides a structural entry point confirming baseline node health and architectural layouts."""
    return {
        "status": "ONLINE",
        "framework": "FastAPI (Python 3.12)",
        "architecture": "BDRA-Lite Modular Monolith Architecture",
        "concurrency_model": "Structured Concurrency (asyncio.TaskGroup)",
        "active_rings": {
            "ring0": "Core Foundation (Identity & Context Validation)",
            "ring1": "Transactional Core (Order Execution, Cache Fallbacks, & WAL)",
            "ring2": "Operational Intelligence (Out-of-band Security Threat Analytics)"
        },
        "interactive_api_docs": "http://127.0.0.1:8080/docs"
    }