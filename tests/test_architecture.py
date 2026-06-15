from pytest_archon import archrule

def test_ring_0_isolation() -> None:
    """Enforces that Ring 0 (Core System Frameworks) has zero knowledge of outer domains."""
    (
        archrule("Ring 0 Core Isolation")
        .match("app.internal.ring0*")
        .should_not_import("app.internal.ring1*")
        .should_not_import("app.internal.ring2*")
        .check("app")
    )


def test_ring_1_isolation() -> None:
    """Enforces that Ring 1 (Core Domain Applications) never imports from Ring 2 Orchestration."""
    (
        archrule("Ring 1 Application Isolation")
        .match("app.internal.ring1*")
        .should_not_import("app.internal.ring2*")
        .check("app")
    )


def test_pure_domain_layer_invariance() -> None:
    """Guarantees that pure business models have absolutely no infrastructure dependencies."""
    (
        archrule("Pure Domain Layer Invariance")
        .match("app.internal.ring*.**.pure*")
        .should_not_import("app.internal.ring*.**.protected*")
        .should_not_import("app.internal.ring*.**.public*")
        # Allow pure components to talk exclusively to other pure elements within boundaries
        .may_import("app.internal.ring*.**.pure*") 
        .check("app")
    )


def test_protected_ports_layer_isolation() -> None:
    """Guarantees that interface contracts do not import concrete transport/driver adapters."""
    (
        archrule("Protected Ports Layer Isolation")
        .match("app.internal.ring*.**.protected*")
        .should_not_import("app.internal.ring*.**.public*")
        .check("app")
    )