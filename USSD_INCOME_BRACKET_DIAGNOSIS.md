# USSD Income-Bracket Live Diagnosis — 2026-07-17T00:08:14.0270185+00:00

## Root cause (identified)
**STALE DEPLOYMENT** — Production Vercel was serving pre–income-bracket USSD code even though GitHub main already contained STATE_REG_INCOME_BRACKET (commit ae3c955, 2026-07-16 23:21:32 UTC).

## Ruled out
1. **Transition-graph gap:** Local/repo state_machine.py correctly sets session["step"] = STATE_REG_INCOME_BRACKET after business type and routes _route to _handle_reg_income_bracket. Not the bug.
2. **Wrong callback URL:** Production POST https://ghana-tax-system-hh6f.vercel.app/ussd/callback/ accepted Arkesel JSON and drove sessions both before and after fix. Capture path /ussd/arkesel-capture/ is same app. Callback URL was not the cause of missing menu (it was serving *old* code correctly for the request).

## Evidence (before redeploy)
- Step labels: "Step 1 of 5" / "Step 2 of 5 - Business Type"
- Business types: Food Vendor first, 6 options, **no Hawker**
- After business type → **Region** (income bracket skipped)

## Evidence (after redeploy of commit 2102585 empty deploy push)
- "Step 2/6 Business Type" with **1. Hawker**
- After business type → **Monthly income:** 1–4 brackets
- Full sim registration returned **GH-TIN-***

## Deploy action
- Empty commit force-push: 2102585 chore(deploy): force production redeploy for USSD income-bracket step
- Detected live ~3–4 minutes after push (poll attempt 7)

## Production sim transcript (Arkesel-shaped)
MSISDN=233231812521
SESSION=livefix-c9a2b8f46b
[1 newSession] Welcome to DA Revenue | 1. Register Business | 2. Check My TIN | 3. Pay Assessment | 4. Help
[2 Register] Step 1 of 6 | Enter your full name:
[3 Name] Step 2/6 Business Type | 1. Hawker | 2. Food Vendor | 3. Clothing | 4. Electronics | 5. Services | 6. Agriculture | 7. Other
[4 BusinessType(1=Hawker)] Monthly income: | 1. GHC 100-400 | 2. GHC 401-1000 | 3. GHC 1001-3000 | 4. GHC 3001+
[5 IncomeBracket(2)] Step 4 of 6 - Region | 1. Greater Accra | 2. Ashanti | 3. Western | 4. Northern | 5. Eastern | 6. Volta | 7. Other
[6 Region(1=GA)] Step 5 of 6 | Enter market or community name:
[7 Market] Step 6 of 6 - Confirm | Name: Live Dial Sim Trader | Business: Hawker | Location: Greater Accra - Makola Demo Market |  | 1. Confirm & Register | 2. Start Over
[8 Confirm] Registration complete! | Your TIN: GH-TIN-D7FD37 | An SMS will be sent shortly.

## Process fix recommendation
After any USSD change: verify production with Arkesel JSON probe (name → business type must return Monthly income / Hawker menu) before assuming shortcode is updated. Git push alone is insufficient if Production alias lags; confirm Production deployment SHA/timestamp.
