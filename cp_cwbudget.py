#!/usr/bin/env python

from gsp import GSP
from util import argmax_index

class Cp_cwbudget:
    """
    Budget-aware balanced bidding agent.
    
    Core strategy:
    - Uses balanced bidding as a base
    - Scales aggression based on remaining budget and time
    - Bids more aggressively when clicks are high (peak hours)
    - Conserves budget when clicks are low (off-peak)
    - Tries to outlast competitors who exhaust their budgets early
    """
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.total_rounds = 48  # known from sim

    def initial_bid(self, reserve):
        return self.value / 2

    def get_spent(self, t, history):
        """Compute actual total spending from historical auction results."""
        spent = 0
        for r in range(t - 1):
            past_round = history.round(r)
            occupants          = past_round.occupants
            per_click_payments = past_round.per_click_payments
            clicks             = past_round.clicks
            for i, occupant in enumerate(occupants):
                if occupant == self.id:
                    spent += per_click_payments[i] * clicks[i]
                    break
        return spent

    def slot_info(self, t, history, reserve):
        prev_round = history.round(t-1)
        other_bids = [(a_id, b) for (a_id, b) in prev_round.bids if a_id != self.id]
        clicks     = prev_round.clicks

        def compute(s):
            (mn, mx) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if mx is None:
                mx = 2 * mn
            return (s, mn, mx)

        return list(map(compute, range(len(clicks))))

    def expected_utils(self, t, history, reserve):
        prev_round = history.round(t-1)
        clicks     = prev_round.clicks
        info       = self.slot_info(t, history, reserve)
        return [clicks[slot] * (self.value - min_bid) for (slot, min_bid, _) in info]

    def target_slot(self, t, history, reserve):
        utils = self.expected_utils(t, history, reserve)
        info  = self.slot_info(t, history, reserve)
        i     = argmax_index(utils)
        return info[i]

    def budget_pace_factor(self, t, history):
        """
        Returns a scaling factor in [0, 1] based on budget consumption pace.
        
        - If we're under-spending relative to time elapsed, be more aggressive (factor > 1 capped at 1)
        - If we're over-spending relative to time elapsed, be more conservative (factor < 1)
        - Preserves a safety reserve for the final rounds
        """
        spent        = self.get_spent(t, history)
        remaining    = self.budget - spent
        rounds_left  = self.total_rounds - t
        
        if rounds_left <= 0:
            return 0.0

        # How much we ideally spend per round
        ideal_spend_rate  = self.budget / self.total_rounds
        # How much we've spent vs how much we should have by now
        expected_spent    = ideal_spend_rate * t
        
        # If we've spent less than expected, we can be more aggressive
        # If we've spent more than expected, pull back
        pace_ratio = expected_spent / max(spent, 1)  # > 1 means under-spent, < 1 means over-spent
        
        # Safety reserve: always keep enough for remaining rounds at half value
        safety_reserve    = rounds_left * (self.value / 4)
        if remaining < safety_reserve:
            return 0.25  # very conservative — nearly out of budget

        # Clamp factor between 0.25 and 1.0
        return min(1.0, max(0.25, pace_ratio))

    def click_factor(self, t, history):
        """
        Returns a scaling factor based on current click volume vs average.
        Bid more aggressively in high-click rounds, conserve in low-click rounds.
        """
        prev_round   = history.round(t-1)
        clicks       = prev_round.clicks
        if not clicks:
            return 1.0
        top_clicks   = clicks[0]

        # From sim: top slot clicks = 30*cos(pi*t/24) + 50, range [20, 80], mean 50
        mean_clicks  = 50
        # Scale: above mean = more aggressive, below mean = less aggressive
        factor       = top_clicks / mean_clicks  # range roughly [0.4, 1.6]
        # Clamp to reasonable range
        return min(1.3, max(0.6, factor))

    def bid(self, t, history, reserve):
        prev_round = history.round(t-1)
        clicks     = prev_round.clicks

        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        # Not expecting to win profitably
        if min_bid >= self.value:
            return self.value

        # Base balanced bid
        if slot == 0:
            bid = self.value
        else:
            util_at_target = clicks[slot] * (self.value - min_bid)
            if clicks[slot - 1] > 0:
                bid = self.value - util_at_target / clicks[slot - 1]
            else:
                bid = min_bid

        # Clamp to slot range
        bid = min(bid, max_bid)
        bid = max(bid, min_bid)

        # Apply click-volume scaling — bid more in high-traffic rounds
        click_scale = self.click_factor(t, history)
        bid = bid * click_scale

        # Apply budget pacing — pull back if overspending, push if underspending
        pace_scale = self.budget_pace_factor(t, history)
        bid = bid * pace_scale

        # Hard budget cap
        spent     = self.get_spent(t, history)
        remaining = self.budget - spent
        bid       = min(bid, remaining)

        return max(bid, 0)

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)