from datamodel import TradingState, OrderDepth, Order
import math

def vwap(order_depth: OrderDepth) -> float | None:
    """
    Top-of-book VWAP with inverted volumes:
    (best_bid * ask_volume + best_ask * bid_volume) / (bid_volume + ask_volume).
    Returns None if either side of the book is empty.
    """
    if not order_depth.buy_orders or not order_depth.sell_orders:
        return None

    best_bid = max(order_depth.buy_orders.keys())
    best_ask = min(order_depth.sell_orders.keys())

    bid_volume = abs(order_depth.buy_orders[best_bid])
    ask_volume = abs(order_depth.sell_orders[best_ask])

    total_volume = bid_volume + ask_volume
    if total_volume == 0:
        return None

    return (best_bid * ask_volume + best_ask * bid_volume) / total_volume


def mid_price(order_depth: OrderDepth) -> float | None:
    """
    Halfway point between the highest bid and lowest ask.
    Returns None if either side of the book is empty.
    """
    if not order_depth.buy_orders or not order_depth.sell_orders:
        return None

    best_bid = max(order_depth.buy_orders.keys())
    best_ask = min(order_depth.sell_orders.keys())

    return (best_bid + best_ask) / 2


ASH_COATED_OSMIUM = "ASH_COATED_OSMIUM"
ASH_COATED_OSMIUM_LIMIT = 80

MEAN_PRICE = 10000
STD_DEV = 10

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
    result = - (diff ** 3)
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
    result = - (math.cbrt(diff))
    if result > 1:
        return 1
    if result < -1:
        return -1
    return result


def calculate_adjustment(price: float, position: int, max_position: int) -> int:
    """
    Calculates the position adjustment based on the price, current position, and maximum position.
    The adjustment is calculated by normalising the price, applying two bounding functions to determine the ideal

    args:
        price: The current price of the asset
        position: The current position in the asset
        max_position: The maximum allowed position in the asset
    """
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

class Trader:
    def run(self, state: TradingState) -> tuple[dict, int, str]:
        result = {}

        orderBook = state.order_depths[ASH_COATED_OSMIUM]
        position = state.position.get(ASH_COATED_OSMIUM, 0)
        limit = ASH_COATED_OSMIUM_LIMIT
        price = int(vwap(orderBook))

        if price is None:
            return result, -1, ""

        positionAdjustment = calculate_adjustment(price, position, limit)

        if positionAdjustment == 0:
            return result, -1, ""
        
        print("Positions:", position, "Price:", price, "normalised_diff:", normalise_diff(price, MEAN_PRICE, STD_DEV), "Adjustment:", positionAdjustment)

        if positionAdjustment > 0:
            best_ask = min(orderBook.sell_orders.keys())
            best_ask_volume = orderBook.sell_orders[best_ask]
            volume = min(positionAdjustment, abs(best_ask_volume))
            result[ASH_COATED_OSMIUM] = [Order(ASH_COATED_OSMIUM, price, volume)]
            print("Buying", volume, "at price", best_ask)
        else:
            best_bid = max(orderBook.buy_orders.keys())
            best_bid_volume = orderBook.buy_orders[best_bid]
            volume = min(positionAdjustment, -best_bid_volume)
            result[ASH_COATED_OSMIUM] = [Order(ASH_COATED_OSMIUM, price, -volume)]
            print("Selling", volume, "at price", best_bid)
        
        conversions = -1
        traderData = ""
        return result, -1, ""