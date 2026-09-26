import pytest

from mananze_os.fulfilment_strategy import FulfilmentStrategy


def make_strategy(**overrides):
    values = {
        "strategy_id": "strategy-001",
        "tenant_id": "tenant-001",
        "strategy_type": "inventory_first",
        "name": "Use available stock first",
    }
    values.update(overrides)
    return FulfilmentStrategy(**values)


def test_valid_strategy() -> None:
    strategy = make_strategy()

    assert strategy.strategy_id == "strategy-001"
    assert strategy.tenant_id == "tenant-001"
    assert strategy.strategy_type == "inventory_first"
    assert strategy.name == "Use available stock first"
    assert strategy.confirmation_status == "unconfirmed"


def test_all_supported_strategy_types() -> None:
    strategy_types = (
        "inventory_first",
        "procurement_after_payment",
        "procurement_before_payment",
        "make_to_order",
        "service_delivery",
        "hybrid",
        "custom",
    )

    for index, strategy_type in enumerate(strategy_types):
        strategy = make_strategy(
            strategy_id=f"strategy-{index}",
            strategy_type=strategy_type,
        )

        assert strategy.strategy_type == strategy_type


def test_all_confirmation_statuses() -> None:
    statuses = (
        "unconfirmed",
        "partially_confirmed",
        "confirmed",
    )

    for status in statuses:
        strategy = make_strategy(
            confirmation_status=status,
        )

        assert strategy.confirmation_status == status


def test_custom_strategy_can_carry_description() -> None:
    strategy = make_strategy(
        strategy_type="custom",
        name="Tenant-specific fulfilment",
        description="Owner-defined fulfilment sequence.",
    )

    assert strategy.description == "Owner-defined fulfilment sequence."


def test_evidence_is_preserved() -> None:
    strategy = make_strategy(
        evidence_ids=("website-001", "owner-confirmation-001"),
    )

    assert strategy.evidence_ids == (
        "website-001",
        "owner-confirmation-001",
    )


def test_blank_strategy_id_rejected() -> None:
    with pytest.raises(ValueError, match="strategy_id is required"):
        make_strategy(strategy_id="")


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        make_strategy(tenant_id="")


def test_blank_strategy_type_rejected() -> None:
    with pytest.raises(ValueError, match="strategy_type is required"):
        make_strategy(strategy_type="")


def test_invalid_strategy_type_rejected() -> None:
    with pytest.raises(ValueError, match="invalid strategy_type"):
        make_strategy(strategy_type="always_buy")  # type: ignore[arg-type]


def test_blank_name_rejected() -> None:
    with pytest.raises(ValueError, match="name is required"):
        make_strategy(name="")


def test_invalid_confirmation_status_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="invalid confirmation_status",
    ):
        make_strategy(
            confirmation_status="assumed",  # type: ignore[arg-type]
        )


def test_blank_evidence_id_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="evidence_ids cannot contain blank values",
    ):
        make_strategy(evidence_ids=("evidence-001", ""))


def test_strategy_is_immutable() -> None:
    strategy = make_strategy()

    with pytest.raises(AttributeError):
        strategy.name = "Changed"


def test_tenant_is_preserved() -> None:
    strategy = make_strategy(tenant_id="tenant-special")

    assert strategy.tenant_id == "tenant-special"
