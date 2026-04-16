from library.datamodel import OrderDepth


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
