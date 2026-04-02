# strat_design3
Strategu Design 3 for Algo Econ, focused on mechanism design


## Balanced Bidding Agent


Key design features: 
 - assume bids stay the same as the last round
 - look at expected utility for each slot. Look at line 52 in  `cp_cwbb.py`
 - after calculating expected utility, you will find max utility and determine appropriate slot
 - from here is where I got slightly confused. You've found optimal slot, and you bid some amount above the current winning amount in order to make you indifferent to the two slots. 
 ## Worked Example (Round 1)

**Setting:**
- `slot_clicks = [80, 60, 45, 34]`
- `slot_occupants = [1, 2, 3, 0]`
- `per_click_payments = [143, 131, 125, 71.5]`
- Agent 4 value = `143` (inferred from `initial_bid = value / 2 = 71.5`)
- Other agents' bids: `[(1, 154), (2, 143), (3, 131), (0, 125)]`

### Step 1 — Utility per slot

| Slot | Clicks | `min_bid` | Utility = `clicks × (value − min_bid)` |
|------|--------|-----------|----------------------------------------|
| 0    | 80     | 143       | 80 × (143 − 143) = **0**              |
| 1    | 60     | 131       | 60 × (143 − 131) = **720**            |
| 2    | 45     | 125       | 45 × (143 − 125) = **810**            |
| 3    | 34     | 71.5      | 34 × (143 − 71.5) = **2431**          |

`target_slot = 3` (highest utility).

### Step 2 — Compute balanced bid

```
util_at_target = 34 × (143 − 71.5) = 2431
b' = 143 − 2431 / 45 = 143 − 54.02 ≈ 88.98
```

Agent 4 should bid **~89 cents** in round 1.

### Step 3 — Sanity check

| Outcome | Calculation | Utility |
|---------|-------------|---------|
| Win slot 3 at `min_bid = 71.5` | 34 × (143 − 71.5) | **2431** |
| Move to slot 2 at bid `b' = 89` | 45 × (143 − 89) | **2430** ✓ |

The near-equality confirms the indifference condition holds — the agent gains nothing by moving up to slot 2.

## Competitive Agent
Our budget-aware agent extends balanced bidding with two additional scaling factors. First, it adjusts bid aggressiveness based on click volume — bidding more in high-traffic rounds and conserving in low-traffic ones, since clicks vary from 20 to 80 per round. Second, it tracks its actual spend rate against an ideal uniform pacing schedule, becoming more aggressive when under-budget and pulling back when over-budget. This pacing strategy is designed to outlast competitors who exhaust their budgets early, allowing our agent to face weaker competition in later rounds. We expect it to perform competitively against pure balanced bidders, particularly in longer auctions where budget constraints become binding.