#!/usr/bin/env python
"""
Reserve price sweep for 5 Cp_cwbb agents.
Run from the same directory as auction.py:
    python reserve_sweep.py
"""

import itertools
import math
import random
import logging
from auction import sim, get_utils, Params
from stats import Stats
from util import mean, stddev, shuffled

logging.disable(logging.INFO)

def run_sweep():
    N_AGENTS   = 5
    MIN_VAL    = 25
    MAX_VAL    = 175
    BUDGET     = 500000
    NUM_ROUNDS = 48
    ITERS      = 10
    MAX_PERMS  = 20
    SEED       = 42

    random.seed(SEED)

    reserve_prices = list(range(110, 140, 1))

    print(f"\n{'Reserve ($)':>12}  {'Avg Daily Revenue ($)':>22}  {'Std Dev ($)':>12}")
    print("-" * 52)

    results = []

    for reserve in reserve_prices:
        total_revenues = []

        for i in range(ITERS):
            values = get_utils(N_AGENTS, type('opt', (), {'min_val': MIN_VAL, 'max_val': MAX_VAL})())

            n_perms = math.factorial(N_AGENTS)
            approx  = n_perms > MAX_PERMS
            perms   = [shuffled(values) for _ in range(MAX_PERMS)] if approx else list(itertools.permutations(values))
            n_perms = MAX_PERMS if approx else n_perms

            total_rev = 0
            for vals in perms:
                config = Params()
                config.add('agent_values', list(vals))
                config.add('agent_class_names', ['Cp_cwbb'] * N_AGENTS)
                config.add('agent_classes', {'Cp_cwbb': __import__('cp_cwbb').Cp_cwbb})
                config.add('budget', BUDGET)
                config.add('reserve', reserve)
                config.add('num_rounds', NUM_ROUNDS)
                config.add('dropoff', 0.75)
                config.add('mechanism', 'gsp')

                history  = sim(config)
                val_dict = dict(zip(range(N_AGENTS), vals))
                total_rev += Stats(history, val_dict).total_revenue()

            total_revenues.append(total_rev / float(n_perms))

        m   = mean(total_revenues)
        std = stddev(total_revenues)
        results.append((reserve, m, std))
        print(f"  {reserve/100:>10.2f}  {m/100:>22.2f}  {std/100:>12.2f}")

    best = max(results, key=lambda x: x[1])
    print("\n" + "=" * 52)
    print(f"  Optimal reserve price : ${best[0]/100:.2f}")
    print(f"  Max avg daily revenue : ${best[1]/100:.2f}  (stddev ${best[2]/100:.2f})")
    print("=" * 52)

if __name__ == "__main__":
    run_sweep()