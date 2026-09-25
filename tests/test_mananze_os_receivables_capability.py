from mananze_os.capability_registry import default_capability_registry


def test_default_registry_contains_receivables():
    registry = default_capability_registry()

    capability = registry.get("receivables")

    assert capability.name == "Receivables Management"
    assert "finance" in capability.domains


def test_default_registry_contains_payment_collection():
    registry = default_capability_registry()

    capability = registry.get("payment_collection")

    assert capability.name == "Payment Collection"
    assert "payments" in capability.domains
