# MANANZE OS — BUILD CONTROL

## Mission

Build one broad, domain-agnostic Mananze AI Operating System.

Mananze learns each real business from authorized evidence, builds Business Truth and a Business Twin, activates applicable capabilities, plans the required workforce, and executes only through governed control-plane boundaries.

## Non-Negotiable Architecture

REAL BUSINESS
→ BUSINESS INTAKE
→ EVIDENCE
→ EVIDENCE ANALYSIS
→ BUSINESS TRUTH
→ BUSINESS TWIN
→ CAPABILITY ACTIVATION
→ WORKFORCE
→ POLICY
→ AUTHORIZATION
→ QA
→ APPROVAL
→ TOOL SELECTION
→ TOOL BINDING
→ GOVERNED TOOL EXECUTION
→ GOVERNED PROVIDER EXECUTION
→ RUNTIME
→ PROVIDER ROUTER
→ PROVIDER GATEWAY
→ REAL WORLD
→ EXECUTION EVIDENCE
→ VERIFICATION
→ DURABLE COMPLETION / RECOVERY

## Tool Architecture

ToolSelector is retained.

ToolSelector is the selection primitive that resolves capability/skill/objective requirements to a registered tool.

ToolSelectionEngine is the governed binding layer. It does not replace ToolSelector's selection responsibility. It adds authoritative binding and validates tenant, skill, permission, provider and execution constraints.

The intended relationship is:

Capability / Skill
→ ToolSelector
→ ToolSelection
→ ToolSelectionEngine
→ ToolBindingPlan
→ GovernedToolExecutionBoundary

## Current Position

All major governed layers through Tool Execution have been built and tested.

CURRENT TASK:
Integrate the existing MananzeRuntime.execute() with the governed tool/provider execution path.

The runtime must stop directly executing providers while retaining:
- durable SQLite task leases
- heartbeat
- idempotency
- recovery
- existing lifecycle state
- approval
- verification
- execution evidence
- provider routing
- provider gateway

## Current Runtime Integration Target

MananzeRuntime.execute()
→ existing workforce execution context
→ ToolSelector / governed ToolSelectionEngine
→ ToolBindingPlan
→ GovernedToolExecutionBoundary
→ GovernedExecutionController
→ GovernedProviderExecutionBoundary
→ RuntimeExecutionBoundary
→ ProviderRouter
→ ProviderExecutionGateway

## Completed Major Layers

- Business Intake
- Evidence Content Ingestion
- PDF/DOCX/XLSX Extraction
- Evidence Analysis
- Business Truth
- Business Twin
- Capability Activation
- Canonical 200-role Workforce
- Capability → Workforce Bridge
- Policy
- Authorization
- Approval
- Action Gate
- Execution Context Integrity
- Durable SQLite Task Execution
- Provider Transport
- Provider Client
- Provider Gateway
- Provider Router
- ToolSelector
- ToolSelectionEngine
- Tool Binding
- Governed Provider Execution
- Governed Tool Execution

## Rules

1. Do not create a second control plane.
2. Do not delete a working layer merely because a new layer was added.
3. Extend existing architecture instead of replacing it without an explicit architectural decision.
4. AI may propose; governance decides.
5. Providers never receive authority directly.
6. Financial-system access remains prohibited unless explicitly authorized.
7. Tenant identity must remain intact through every boundary.
8. Every external action must have traceable governance lineage.
9. Durable execution and idempotency must survive provider retries/restarts.
10. Every completed architectural step must have tests.
11. Focused tests first, full suite second.
12. Do not call an isolated boundary "integrated" until the real runtime uses it.

## Build Rhythm

1. Read this control document.
2. Identify CURRENT TASK.
3. Inspect only the exact code needed for that task.
4. Implement the smallest architectural change.
5. Add/adjust tests.
6. Run focused tests.
7. Run full pytest.
8. Run git diff --check.
9. Commit only when green.
10. Update this document.
11. Move to the next task.

## Current Known Architectural Debt

- Capability activation provenance should preserve true Business Truth IDs.
- Capability evidence rules need tighter semantics.
- Financial capabilities need explicit operational-access restrictions.
- Provider health/usage/cost ledgers should eventually become durable and tenant-scoped.
- Runtime still contains legacy direct tool/provider execution integration and is the current task.
