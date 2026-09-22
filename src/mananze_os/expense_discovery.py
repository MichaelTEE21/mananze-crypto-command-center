"""Mananze OS expense discovery and supplier intelligence."""

from dataclasses import dataclass

from mananze_os.payment_solution_intelligence import ExpenseRecord


EvidenceStatus = str


@dataclass(frozen=True)
class ExpenseEvidence:
    evidence_id: str
    tenant_id: str
    source_type: str
    source_reference: str
    evidence_status: EvidenceStatus = "client_provided"
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.source_type.strip():
            raise ValueError("source_type is required")
        if not self.source_reference.strip():
            raise ValueError("source_reference is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class SupplierProfile:
    supplier_id: str
    tenant_id: str
    name: str
    categories: tuple[str, ...] = ()
    recurring_expense_count: int = 0
    total_expense_value: float = 0.0

    def __post_init__(self) -> None:
        if not self.supplier_id.strip():
            raise ValueError("supplier_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if self.recurring_expense_count < 0:
            raise ValueError("recurring_expense_count cannot be negative")
        if self.total_expense_value < 0:
            raise ValueError("total_expense_value cannot be negative")


@dataclass(frozen=True)
class ExpenseDiscoveryResult:
    tenant_id: str
    expenses: tuple[ExpenseRecord, ...]
    evidence: tuple[ExpenseEvidence, ...]
    suppliers: tuple[SupplierProfile, ...]


class ExpenseDiscovery:
    """Discover structured expense intelligence from supplied evidence.

    Discovery does not grant financial access and does not execute payments.
    """

    def discover(
        self,
        tenant_id: str,
        expenses: tuple[ExpenseRecord, ...],
        evidence: tuple[ExpenseEvidence, ...] = (),
    ) -> ExpenseDiscoveryResult:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        tenant_expenses = tuple(
            expense
            for expense in expenses
            if expense.tenant_id == tenant_id
        )

        tenant_evidence = tuple(
            item
            for item in evidence
            if item.tenant_id == tenant_id
        )

        supplier_map: dict[str, list[ExpenseRecord]] = {}

        for expense in tenant_expenses:
            supplier_map.setdefault(expense.supplier, []).append(expense)

        suppliers: list[SupplierProfile] = []

        for supplier_name in sorted(supplier_map):
            supplier_expenses = supplier_map[supplier_name]

            categories = tuple(
                sorted({expense.category for expense in supplier_expenses})
            )

            recurring_count = sum(
                expense.recurring for expense in supplier_expenses
            )

            total_value = sum(
                expense.amount for expense in supplier_expenses
            )

            suppliers.append(
                SupplierProfile(
                    supplier_id=f"supplier:{supplier_name.lower().replace(' ', '-')}",
                    tenant_id=tenant_id,
                    name=supplier_name,
                    categories=categories,
                    recurring_expense_count=recurring_count,
                    total_expense_value=total_value,
                )
            )

        return ExpenseDiscoveryResult(
            tenant_id=tenant_id,
            expenses=tenant_expenses,
            evidence=tenant_evidence,
            suppliers=tuple(suppliers),
        )


__all__ = [
    "ExpenseEvidence",
    "SupplierProfile",
    "ExpenseDiscoveryResult",
    "ExpenseDiscovery",
]
