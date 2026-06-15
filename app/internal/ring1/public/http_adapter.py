import secrets
from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, HTTPException, status, Depends
from pydantic import BaseModel

from app.internal.ring0.protected.context import set_tenant_context, clear_tenant_context
from app.internal.ring1.pure.order import create_order, InvalidAmountError
from app.internal.ring1.public.resilient_repo import ResilientOrderRepository

router = APIRouter()

# Global pointer initialized by main.py composition root
_global_repo: Optional[ResilientOrderRepository] = None


class OrderRequest(BaseModel):
    """Pydantic model validating inbound JSON request bodies."""
    user_id: str
    amount: float


def get_repo() -> ResilientOrderRepository:
    """Dependency provider guaranteeing repository availability to delivery layers."""
    if _global_repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System core engine initializing. Please retry shortly."
        )
    return _global_repo


@router.post("/orders")
async def create_order_endpoint(
    payload: OrderRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    repo: ResilientOrderRepository = Depends(get_repo)
) -> Dict[str, Any]:
    """Inbound HTTP adapter orchestrating a transaction inside a scoped multi-tenant safety barrier."""
    # 1. Capture the structural isolation token returned by the context manager
    token = set_tenant_context(x_tenant_id)
    
    try:
        # 2. Allocate an explicit ID and run pure business invariants
        generated_id = f"ord_{secrets.token_hex(4)}"
        order = create_order(generated_id, payload.user_id, payload.amount)
        
        # 3. Request write commit from the resilient storage adapter
        # NOTE: If your repository method is named 'save_order', change this to repo.save_order(order)
        await repo.save(order)
        
        return {
            "status": "SUCCESS",
            "message": "Transaction safely verified and recorded.",
            "data": {
                "id": order.id,
                "user_id": order.user_id,
                "amount": order.amount
            }
        }
    except InvalidAmountError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    finally:
        # 4. Pass the token back to cleanly unwind the async context variable state
        clear_tenant_context(token)


@router.get("/orders/{order_id}")
async def get_order_endpoint(
    order_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    repo: ResilientOrderRepository = Depends(get_repo)
) -> Dict[str, Any]:
    """Resolves transactions, using memory read caches seamlessly if database lines are down."""
    token = set_tenant_context(x_tenant_id)
    try:
        # 1. Invoke the real database retrieval method
        order_data = await repo.find(order_id)
        
        # 2. Assert data presence safely inside our multi-tenant boundary
        if order_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order '{order_id}' could not be located inside Tenant workspace."
            )
            
        # 3. Access keys using safe dictionary indexing to satisfy strict type narrowing
        return {
            "status": "SUCCESS",
            "data": {
                "id": str(order_data.get("id", order_id)),
                "user_id": str(order_data.get("user_id", "")),
                "amount": float(order_data.get("amount", 0.0))
            }
        }
    finally:
        clear_tenant_context(token)
