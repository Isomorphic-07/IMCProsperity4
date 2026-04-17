from src.library.datamodel import TradingState, OrderDepth, Order
from src.traderTemplate import Trader
from src.library.constants import ASH_COATED_OSMIUM, ASH_COATED_OSMIUM_LIMIT, BUY, SELL

def bid_ask_spread(depth: OrderDepth) -> tuple[int, int] | None:
    if not depth.buy_orders or not depth.sell_orders:
        return None
    best_bid = max(depth.buy_orders.keys())
    best_ask = min(depth.sell_orders.keys())
    return (best_bid, best_ask)

class MarketMaker(Trader):
    def run(self, state: TradingState) -> tuple[dict, int, str]:
        result = {}

        orderBook = state.order_depths.get(ASH_COATED_OSMIUM, None)
        if orderBook is None:
            return {}, -1, ""
        position = state.position.get(ASH_COATED_OSMIUM, 0)
        limit = ASH_COATED_OSMIUM_LIMIT
        spread = bid_ask_spread(orderBook)
        if spread is None:
            return {}, -1, ""
        bestBid, bestAsk = spread
        bidPrice, askPrice = bestBid + 1, bestAsk - 1
        volume = 30

        print(f"Position: {position}")
        if bestAsk - bestBid > 8:
            buy_order = Order(ASH_COATED_OSMIUM, bidPrice, volume * BUY)
            sell_order = Order(ASH_COATED_OSMIUM, askPrice, volume * SELL)
            print(f"<<{bidPrice} at {askPrice} {volume} UP>>")
            result[ASH_COATED_OSMIUM] = [buy_order, sell_order]

        return result, -1, ""