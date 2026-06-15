import contextvars

# Thread-safe and coroutine-local storage primitive
_tenant_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id")

def set_tenant_context(tenant_id: str) -> contextvars.Token[str]:
    """Binds a tenant ID string to the active asynchronous task execution chain."""
    return _tenant_id_var.set(tenant_id)

def get_tenant_context() -> str:
    """Retrieves the active tenant ID context or triggers a boundary security breach crash."""
    try:
        return _tenant_id_var.get()
    except LookupError:
        raise RuntimeError("Boundary Security Fault: Context execution invoked without a valid tenant assignment.")

def clear_tenant_context(token: contextvars.Token[str]) -> None:
    """Resets the context block cleanly to prevent cross-tenant memory leakage across tasks."""
    _tenant_id_var.reset(token)