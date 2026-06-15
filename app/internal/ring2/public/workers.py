import asyncio
from typing import Dict, List, Optional
from app.internal.ring1.public.resilient_repo import ResilientOrderRepository
from app.internal.ring2.pure.risk import evaluate_order_risk, RiskAssessment
from app.internal.ring2.protected.ports import RiskSnapshotDTO

class OutboxStreamingWorker:
    """Asynchronous consumer processing outbox events and recording security risk profiles."""
    
    def __init__(self, repo: ResilientOrderRepository):
        self.repo = repo
        self.risk_ledger: Dict[str, List[RiskAssessment]] = {}
        self._lock = asyncio.Lock()

    async def start_streaming_loop(self, shutdown_event: asyncio.Event) -> None:
        """Consumes messages from the transactional stream without adding user latency."""
        queue = self.repo.outbox_queue
        while not shutdown_event.is_set() or not queue.empty():
            try:
                event_data = await asyncio.wait_for(queue.get(), timeout=0.2)
                tenant_id = event_data["tenant_id"]
                order_id = event_data["data"]["id"]
                amount = event_data["data"]["amount"]
                
                # Execute our pure, deterministic Ring 2 risk rule
                assessment = evaluate_order_risk(tenant_id, order_id, amount)
                
                # If it's a high-risk security anomaly, log it to the ledger inside a thread lock
                if assessment.requires_manual_review:
                    async with self._lock:
                        if tenant_id not in self.risk_ledger:
                            self.risk_ledger[tenant_id] = []
                        self.risk_ledger[tenant_id].append(assessment)
                    
                    print(f"⚠️ [RING 2 WORKER] Threat detected for Tenant '{tenant_id}' on Order '{order_id}'! Score: {assessment.fraud_score}")
                
                queue.task_done()
            except asyncio.TimeoutError:
                continue

    async def get_tenant_risk_profile(self, tenant_id: str) -> Optional[RiskSnapshotDTO]:
        """Satisfies the contract interface allowing external actors to safely read compiled metrics."""
        async with self._lock:
            assessments = self.risk_ledger.get(tenant_id, [])
            if not assessments:
                return None
            return RiskSnapshotDTO(
                tenant_id=tenant_id,
                high_risk_count=len(assessments)
            )