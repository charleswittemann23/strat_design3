#!/usr/bin/env python

import sys
from gsp import GSP
from util import argmax_index

class Cp_cwbb:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget

    def initial_bid(self, reserve):
        return self.value / 2

    def get_spent(self, t, history):
        """Compute actual total spending from historical auction results."""
        spent = 0
        for r in range(t - 1):
            past_round = history.round(r)
            occupants = past_round.occupants          # was wrongly called 'allocation'
            per_click_payments = past_round.per_click_payments
            clicks = past_round.clicks

            for i, occupant in enumerate(occupants):
                if occupant == self.id:
                    spent += per_click_payments[i] * clicks[i]
                    break
        return spent

    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        other_bids = [a_id_b for a_id_b in prev_round.bids if a_id_b[0] != self.id]
        clicks = prev_round.clicks

        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max is None:
                max = 2 * min
            return (s, min, max)

        return list(map(compute, list(range(len(clicks)))))

    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        Returns a list of utilities, one per slot (same length as slot_info).
        """
        prev_round = history.round(t-1)
        clicks = prev_round.clicks
        info = self.slot_info(t, history, reserve)

        utilities = [clicks[slot] * (self.value - min_bid)
                     for (slot, min_bid, _) in info]
        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid).
        """
        utils = self.expected_utils(t, history, reserve)
        info = self.slot_info(t, history, reserve)
        i = argmax_index(utils)
        return info[i]

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # - targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - t_s(j))}.
        # - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - t_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # If s*_j is the top slot, bid the value v_j

        prev_round = history.round(t-1)
        clicks = prev_round.clicks

        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        # Spec: if price at target >= value, not expecting to win profitably -> bid value
        if min_bid >= self.value:
            return self.value

        if slot == 0:
            # Going for the top slot: bid full value
            bid = self.value
        else:
            # Balanced bidding equation:
            # clicks[slot] * (value - min_bid) = clicks[slot-1] * (value - bid)
            # => bid = value - clicks[slot] * (value - min_bid) / clicks[slot-1]
            util_at_target = clicks[slot] * (self.value - min_bid)
            if clicks[slot - 1] > 0:
                bid = self.value - util_at_target / clicks[slot - 1]
            else:
                bid = min_bid

        # Clamp bid to valid range for the target slot
        bid = min(bid, max_bid)
        bid = max(bid, min_bid)

        # Budget enforcement: cap against actual remaining budget from history
        remaining = self.budget - self.get_spent(t, history)
        bid = min(bid, remaining)

        return max(bid, 0)

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)