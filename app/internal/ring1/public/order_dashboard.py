from typing import Dict, Any
from fastapi import APIRouter, Depends

from app.internal.ring1.public.resilient_repo import ResilientOrderRepository
from app.internal.ring1.public.http_adapter import get_repo

router = APIRouter()


@router.get("/dashboard/metrics")
async def get_metrics_endpoint(
    repo: ResilientOrderRepository = Depends(get_repo)
) -> Dict[str, Any]:  # 👈 Mypy Fix: Explicit return type annotation
    """Exposes a read-only telemetry dashboard endpoint for system monitoring."""
    
    # Safely look up cache sizes to protect against empty initial states
    cached_count = len(repo.read_cache) if hasattr(repo, 'read_cache') else 0
    wal_count = len(repo.wal_queue) if hasattr(repo, 'wal_queue') else 0
    outbox_count = repo.outbox_queue.qsize() if hasattr(repo, 'outbox_queue') else 0

    return {
        "system_status": "OPERATIONAL",
        "telemetry": {
            "tier_2_cached_reads_count": cached_count,
            "tier_1_pending_wal_logs": wal_count,
            "ring_2_pending_outbox_events": outbox_count
        }
    }