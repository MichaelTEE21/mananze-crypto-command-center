---
category: ADVANCED
related: l1_l2, bridges
---
# Zero-knowledge (ZK) basics

ZK proofs let a prover convince a verifier a statement is true without revealing the underlying witness (within the cryptography’s assumptions).

## In crypto systems
- **Validity proofs** for L2 state transitions
- Privacy tech (selective disclosure) — threat models vary widely
- Circuits / proving systems have audit and bug surfaces

## Researcher checklist
1. What exactly is proven? What remains trusted (sequencer, DAC, committee)?
2. Trusted setup or transparent setup? Ceremony docs?
3. Audit dates and scope for circuits + verifier contracts
4. Label performance claims (TPS, cost) with source + timestamp — else unavailable

## Warnings
- “ZK” in a name is marketing until you read the proof system and trust model.
- Complex cryptography increases implementation risk — prefer primary papers/docs.

> Not financial advice. Education only.
