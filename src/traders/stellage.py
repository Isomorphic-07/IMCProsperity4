from src.traderTemplate import Trader
from src.library.pricers import vwap, mid_price
from src.library.datamodel import TradingState, OrderDepth, Order
from src.library.constants import ASH_COATED_OSMIUM, ASH_COATED_OSMIUM_LIMIT

MEAN_PRICE = 10000
STD_DEV = 30

def normalise_diff(price: float, average_price: float, deviation: float) -> float:
    """
    Normalises the price to a value between -1 and 1, representing how far the 
    price is from the average price in terms of standard deviations.
    """
    return (price - average_price) / deviation

def bound_function1(diff: float) -> float:
    """
    This function takes a price and returns a value between -1 and 1, representing the
    normalised position that should be taken based on the price.

    args:
        diff: A normalised difference between the average price and current price
    """
    result = diff ** 3
    if result > 1:
        return 1
    if result < -1:
        return -1
    return result

def bound_function2(diff: float) -> float:
    """
    This function takes a price and returns a value between -1 and 1, representing the
    normalised position that should be taken based on the price.

    args:
        price: A normalised difference between the average price and current price
    """
    result = diff ** 3
    if result > 1:
        return 1
    if result < -1:
        return -1
    return result


def calculate_adjustment(price: float, position: int, max_position: int) -> int:
    normalised_diff = normalise_diff(price, MEAN_PRICE, STD_DEV)
    boundaries = [bound_function1(normalised_diff), bound_function2(normalised_diff)]
    boundaries.sort()

    if position < int(boundaries[0] * max_position):
        ideal_position = int(boundaries[0] * max_position)
        return ideal_position - position
    
    if position > int(boundaries[1] * max_position):
        ideal_position = int(boundaries[1] * max_position)
        return ideal_position - position

    return 0

class StellageTrader(Trader):
    def run(self, state: TradingState) -> tuple[dict, int, str]:
        result = {}

        orderBook = state.order_depths[ASH_COATED_OSMIUM]
        position = state.position[ASH_COATED_OSMIUM]
        limit = ASH_COATED_OSMIUM_LIMIT
        price = vwap(orderBook)

        if price is None:
            return result, -1, ""

        positionAdjustment = calculate_adjustment(price, position, limit)

        if positionAdjustment == 0:
            return result, -1, ""
        
        if positionAdjustment > 0:
            best_ask = min(orderBook.sell_orders.keys())
            best_ask_volume = orderBook.sell_orders[best_ask]
            volume = min(positionAdjustment, best_ask_volume)
            result[ASH_COATED_OSMIUM] = Order(ASH_COATED_OSMIUM, best_ask, volume)
        else:
            best_bid = max(orderBook.buy_orders.keys())
            best_bid_volume = orderBook.buy_orders[best_bid]
            volume = min(-positionAdjustment, best_bid_volume)
            result[ASH_COATED_OSMIUM] = Order(ASH_COATED_OSMIUM, best_bid, -volume)
        
        conversions = -1
        traderData = ""
        return result, -1, ""