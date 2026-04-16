import unittest

from src.traders.stellage import (
    MEAN_PRICE,
    STD_DEV,
    StellageTrader,
    bound_function1,
    bound_function2,
    calculate_adjustment,
    normalise_diff,
)
from src.library.datamodel import Observation, OrderDepth, TradingState
from src.library.constants import ASH_COATED_OSMIUM, ASH_COATED_OSMIUM_LIMIT


def make_order_depth(buys=None, sells=None) -> OrderDepth:
    od = OrderDepth()
    od.buy_orders = dict(buys or {})
    od.sell_orders = dict(sells or {})
    return od


def make_state(order_depth: OrderDepth, position: int) -> TradingState:
    return TradingState(
        traderData="",
        timestamp=0,
        listings={},
        order_depths={ASH_COATED_OSMIUM: order_depth},
        own_trades={},
        market_trades={},
        position={ASH_COATED_OSMIUM: position},
        observations=Observation(plainValueObservations={}, conversionObservations={}),
    )


class TestNormaliseDiff(unittest.TestCase):
    def test_price_equals_mean_returns_zero(self):
        self.assertEqual(normalise_diff(10000, 10000, 30), 0.0)

    def test_one_std_above(self):
        self.assertAlmostEqual(normalise_diff(10030, 10000, 30), 1.0)

    def test_one_std_below(self):
        self.assertAlmostEqual(normalise_diff(9970, 10000, 30), -1.0)

    def test_fractional_std(self):
        self.assertAlmostEqual(normalise_diff(10015, 10000, 30), 0.5)

    def test_multiple_std_above(self):
        self.assertAlmostEqual(normalise_diff(10090, 10000, 30), 3.0)


class TestBoundFunction1(unittest.TestCase):
    # bound_function1(diff) = -(diff**3), clipped to [-1, 1].
    # Mean-reversion: above mean -> negative (short), below mean -> positive (long).
    def test_zero(self):
        self.assertEqual(bound_function1(0), 0)

    def test_small_positive_cubed_and_negated(self):
        self.assertAlmostEqual(bound_function1(0.5), -0.125)

    def test_small_negative_cubed_and_negated(self):
        self.assertAlmostEqual(bound_function1(-0.5), 0.125)

    def test_boundary_one_flips_to_negative_one(self):
        self.assertEqual(bound_function1(1), -1)

    def test_boundary_negative_one_flips_to_one(self):
        self.assertEqual(bound_function1(-1), 1)

    def test_clipped_when_positive_input_exceeds_one(self):
        self.assertEqual(bound_function1(2), -1)

    def test_clipped_when_negative_input_exceeds_one(self):
        self.assertEqual(bound_function1(-2), 1)

    def test_just_above_one_clipped_to_negative_one(self):
        self.assertEqual(bound_function1(1.5), -1)


class TestBoundFunction2(unittest.TestCase):
    # bound_function2(diff) = -cbrt(diff), clipped to [-1, 1].
    def test_zero(self):
        self.assertEqual(bound_function2(0), 0)

    def test_boundary_one_flips_to_negative_one(self):
        self.assertAlmostEqual(bound_function2(1), -1)

    def test_boundary_negative_one_flips_to_one(self):
        self.assertAlmostEqual(bound_function2(-1), 1)

    def test_positive_input_negated(self):
        # cbrt(0.125) = 0.5 -> -0.5
        self.assertAlmostEqual(bound_function2(0.125), -0.5)

    def test_negative_input_negated(self):
        # cbrt(-0.125) = -0.5 -> 0.5
        self.assertAlmostEqual(bound_function2(-0.125), 0.5)

    def test_cbrt_above_one_clipped(self):
        # cbrt(8) = 2 -> -2 -> clipped to -1
        self.assertEqual(bound_function2(8), -1)

    def test_cbrt_below_negative_one_clipped(self):
        # cbrt(-8) = -2 -> 2 -> clipped to 1
        self.assertEqual(bound_function2(-8), 1)

    def test_agrees_with_bound_function1_at_shared_fixed_points(self):
        # Share fixed points {-1 -> 1, 0 -> 0, 1 -> -1}; both clip past boundaries.
        for diff in [-3, -1, 0, 1, 2.5]:
            self.assertAlmostEqual(bound_function2(diff), bound_function1(diff))


class TestCalculateAdjustment(unittest.TestCase):
    # Boundaries are [bf1(diff), bf2(diff)] sorted; position is pushed into that band.
    def test_at_mean_flat_position_no_adjustment(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE, 0, 80), 0)

    def test_at_mean_long_position_sells_down_to_zero(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE, 10, 80), -10)

    def test_at_mean_short_position_buys_up_to_zero(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE, -5, 80), 5)

    def test_one_std_above_targets_full_short(self):
        # diff = 1 -> bf1 = bf2 = -1 -> ideal = -80
        self.assertEqual(calculate_adjustment(MEAN_PRICE + STD_DEV, 0, 80), -80)

    def test_one_std_below_targets_full_long(self):
        # diff = -1 -> bf1 = bf2 = 1 -> ideal = 80
        self.assertEqual(calculate_adjustment(MEAN_PRICE - STD_DEV, 0, 80), 80)

    def test_above_mean_no_adjustment_when_already_at_short_target(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE + STD_DEV, -80, 80), 0)

    def test_below_mean_no_adjustment_when_already_at_long_target(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE - STD_DEV, 80, 80), 0)

    def test_far_above_mean_clipped_to_full_short(self):
        # diff = 10 -> -diff**3 = -1000 clipped to -1
        self.assertEqual(calculate_adjustment(MEAN_PRICE + 10 * STD_DEV, 0, 80), -80)

    def test_far_below_mean_clipped_to_full_long(self):
        self.assertEqual(calculate_adjustment(MEAN_PRICE - 10 * STD_DEV, 0, 80), 80)

    def test_overshot_short_position_is_trimmed_back(self):
        # Above mean wants -80; position = -100 is past that -> buy 20 back.
        self.assertEqual(calculate_adjustment(MEAN_PRICE + STD_DEV, -100, 80), 20)

    def test_overshot_long_position_is_trimmed_back(self):
        # Below mean wants 80; position = 100 is past that -> sell 20 back.
        self.assertEqual(calculate_adjustment(MEAN_PRICE - STD_DEV, 100, 80), -20)


class TestStellageTraderRun(unittest.TestCase):
    def test_returns_empty_when_book_empty(self):
        trader = StellageTrader()
        state = make_state(make_order_depth(), position=0)
        result, conversions, data = trader.run(state)
        self.assertEqual(result, {})
        self.assertEqual(conversions, -1)
        self.assertEqual(data, "")

    def test_returns_empty_when_no_adjustment_needed(self):
        # VWAP = 10000 -> diff 0 -> no trade.
        trader = StellageTrader()
        od = make_order_depth(buys={9999: 5}, sells={10001: 5})
        state = make_state(od, position=0)
        result, conversions, data = trader.run(state)
        self.assertEqual(result, {})
        self.assertEqual(conversions, -1)
        self.assertEqual(data, "")

    def test_places_buy_order_when_price_below_mean(self):
        # VWAP ~ 9970 -> ideal +80 -> buy at best ask.
        trader = StellageTrader()
        best_ask = 9971
        od = make_order_depth(buys={9969: 10}, sells={best_ask: 5})
        state = make_state(od, position=0)
        result, _, _ = trader.run(state)
        self.assertIn(ASH_COATED_OSMIUM, result)
        order = result[ASH_COATED_OSMIUM]
        self.assertEqual(order.symbol, ASH_COATED_OSMIUM)
        self.assertEqual(order.price, best_ask)
        self.assertGreater(order.quantity, 0)

    def test_places_sell_order_when_price_above_mean(self):
        # VWAP ~ 10030 -> ideal -80 -> sell at best bid.
        trader = StellageTrader()
        best_bid = 10029
        od = make_order_depth(buys={best_bid: 5}, sells={10031: 10})
        state = make_state(od, position=0)
        result, _, _ = trader.run(state)
        self.assertIn(ASH_COATED_OSMIUM, result)
        order = result[ASH_COATED_OSMIUM]
        self.assertEqual(order.symbol, ASH_COATED_OSMIUM)
        self.assertEqual(order.price, best_bid)
        self.assertLess(order.quantity, 0)

    def test_buy_volume_capped_by_best_ask_size(self):
        # Wants to buy 80 but only 3 available at best ask.
        trader = StellageTrader()
        best_ask = 9971
        od = make_order_depth(buys={9969: 10}, sells={best_ask: 3})
        state = make_state(od, position=0)
        result, _, _ = trader.run(state)
        self.assertEqual(result[ASH_COATED_OSMIUM].quantity, 3)

    def test_sell_volume_capped_by_best_bid_size(self):
        trader = StellageTrader()
        best_bid = 10029
        od = make_order_depth(buys={best_bid: 4}, sells={10031: 10})
        state = make_state(od, position=0)
        result, _, _ = trader.run(state)
        self.assertEqual(result[ASH_COATED_OSMIUM].quantity, -4)

    def test_uses_configured_position_limit(self):
        # Sanity: constant matches what the trader is wired to use.
        self.assertEqual(ASH_COATED_OSMIUM_LIMIT, 80)


if __name__ == "__main__":
    unittest.main()
