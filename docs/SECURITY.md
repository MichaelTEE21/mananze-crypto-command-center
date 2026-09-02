# MCCC Security Notes

## Never store / accept

- Seed phrases, recovery phrases, mnemonics  
- Private keys / hex privkeys  
- Wallet or exchange passwords, 2FA/OTP secrets  

Enforced via `mccc.security.reject_sensitive_credential` on auth, wallets, AI, notes.

## App accounts

- Passwords: stdlib **scrypt**; never logged.  
- Guest mode is first-class.  
- Soft-delete scrubs password hash.  
- `AUTH_SECRET` for session salt — set in production.  
- No email password-reset pipeline yet — use signed-in **Change password** on Account.

## Public donation addresses

BTC / ETH / SOL donation addresses are **public** (not secrets). Configure via:

- `MCCC_BTC_DONATION_ADDRESS`  
- `MCCC_ETH_DONATION_ADDRESS`  
- `MCCC_SOL_DONATION_ADDRESS`  

Defaults match documented public addresses. UI warns users to verify network and never send seeds.

## Data honesty

- Never fabricate chain balances, txs, TVL, unlocks, burns, donation totals.  
- Label **DEMO** / **DATA UNAVAILABLE**.  
- Analyst vocabulary: **VERIFIED** (sourced), **CALCULATED** (derived from retrieved data), **INFERENCE** (explicitly labelled opinion).

## Deploy secrets

- Never commit API keys, Render credentials, admin passwords.  
- Partner referral URLs live in DB admin UI — not hardcoded in pages.

## Postgres migration path (future)

1. Keep SQLite working (`MCCC_DB_PATH`).  
2. When ready: provision Postgres, set `DATABASE_URL`, implement dual-path adapter behind `db.connect`.  
3. Migrate with explicit dump/load; do not switch free Render mid-flight without disk + backup.  
4. Until then `DATABASE_URL` is ignored with a startup warning.
