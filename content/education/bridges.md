---
category: INTERMEDIATE
related: l1_l2, defi_basics, scams
---
# Bridges

Cross-chain bridges move assets or messages between networks. They are high-value attack targets.

## How they typically work
- Lock-and-mint, burn-and-mint, or liquidity-pool models
- Relayers / validators attest that an event happened on the source chain
- Destination chain releases or mints after verification

## Diligence checklist
1. Who custody funds during transit? Multisig? Light client? Optimistic challenge?
2. Is there an official docs URL + audited contracts (dated)?
3. What happens on pause / upgrade / emergency withdrawal?
4. Prefer small test transfers; verify explorer txs yourself.

## Warnings
- Fake “bridge UI” phishing sites are common — bookmark official URLs offline.
- Bridging does not remove token or smart-contract risk on the destination chain.
- Never paste seed phrases into bridge “recovery” forms.

> Not financial advice. Education only. Bridge hacks have caused large historical losses.
