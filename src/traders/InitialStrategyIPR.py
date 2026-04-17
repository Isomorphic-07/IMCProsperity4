from datamodel import TradingState, OrderDepth, Order
import math

ASH_COATED_OSMIUM = "ASH_COATED_OSMIUM"
ASH_COATED_OSMIUM_LIMIT = 80

INTARIAN_PEPPER_ROOT = "INTARIAN_PEPPER_ROOT"
INTARIAN_PEPPER_ROOT_LIMIT = 80

MEAN_PRICE = 10000
STD_DEV = 10

BUY = 1
SELL = -1


class Trader:
    def __init__(self):
        # State of pepper algorithm
        # 0 -> Neutral
        # 1 -> Shorting
        # -1 -> Buying
        self.pepperState = 0
        self.ashState = 0

    def run(self, state: TradingState) -> tuple[dict, int, str]:
        result = {}

        outgoingAshOrders = self.runAshMarketMaker(
            state,
            ASH_COATED_OSMIUM,
            ASH_COATED_OSMIUM_LIMIT
        )
        if (outgoingAshOrders is not None):
            result[ASH_COATED_OSMIUM] = outgoingAshOrders

        outgoingPepperOrders = self.runPepper(
            state,
            INTARIAN_PEPPER_ROOT,
            INTARIAN_PEPPER_ROOT_LIMIT
        )
        if (outgoingPepperOrders is not None):
            result[INTARIAN_PEPPER_ROOT] = outgoingPepperOrders

        conversions = -1
        traderData = ""
        return result, conversions, traderData

    def runAshMarketMaker(self, state: TradingState, symbol: str, limit: int):

        orderBook = state.order_depths.get(symbol, None)
        if orderBook is None:
            return None
        position = state.position.get(symbol, 0)
        spread = bid_ask_spread(orderBook)
        if spread is None:
            return None
        bestBid, bestAsk = spread
        bidPrice, askPrice = bestBid + 1, bestAsk - 1
        volume = 30

        print(f"Position: {position}")
        if bestAsk - bestBid > 8:
            buy_order = Order(symbol, bidPrice, volume * BUY)
            sell_order = Order(symbol, askPrice, volume * SELL)
            print(f"<<{bidPrice} at {askPrice} {volume} UP>>")
            return [buy_order, sell_order]

        return None

    def runAsh2(
            self,
            state: TradingState,
            symbol: str,
            limit: int
    ):
        orderBook = state.order_depths[symbol]
        position = state.position.get(symbol, 0)

        price = vwap(orderBook)

        if price is None:
            return None
        price = int(price)

        fairPrice = 10000

        z = (price - fairPrice) / 5.35

        if (self.ashState == 0):
            if (z > 2.0):
                self.ashState = 1
            elif (z < -2.0):
                self.ashState = -1

        if (self.ashState == 1):

            # Sell
            if (z > 2.0):
                bestBid = max(orderBook.buy_orders.keys())
                bestBidVolume = orderBook.buy_orders[bestBid]
                volume = min(abs(limit + position), abs(bestBidVolume))

                if (volume > 0):
                    return [Order(symbol, bestBid, -volume)]
                return None
            if (z > 0.5):
                return None

            # Exit the position, and buy at that price
            if (position < 0):
                bestAsk = min(orderBook.sell_orders.keys())
                bestAskVolume = orderBook.sell_orders[bestAsk]
                volume = min(abs(position), abs(bestAskVolume))

                if (volume > 0):
                    return [Order(symbol, bestAsk, volume)]
                return None

            # Reset state to neutral after all inventory cleared
            self.ashState = 0

        if (self.ashState == -1):

            # Buy
            if (z < -2.0):
                bestAsk = min(orderBook.sell_orders.keys())
                bestAskVolume = orderBook.sell_orders[bestAsk]
                volume = min(abs(position - limit), abs(bestAskVolume))

                if (volume > 0):
                    return [Order(symbol, bestAsk, volume)]
                return None

            if (z < -0.5):
                return None

            # Exit the position, and sell
            if (position > 0):
                bestBid = max(orderBook.buy_orders.keys())
                bestBidVolume = orderBook.buy_orders[bestBid]
                volume = min(abs(position), abs(bestBidVolume))

                if (volume > 0):
                    return [Order(symbol, bestBid, -volume)]
                return None

            # Reset state to neutral after all inventory cleared
            self.ashState = 0

        return None

    def runAsh(
            self,
            state: TradingState,
            symbol: str,
            limit: int
    ) -> list[Order] | None:

        orderBook = state.order_depths[symbol]
        position = state.position.get(symbol, 0)
        price = int(vwap(orderBook))

        if price is None:
            return None

        positionAdjustment = calculate_adjustment(price, position, limit)

        if (positionAdjustment == 0):
            return None

        print(
            "Positions:", position,
            "Price:", price,
            "normalised_diff:", normalise_diff(price, MEAN_PRICE, STD_DEV),
            "Adjustment:", positionAdjustment
        )

        if positionAdjustment > 0:
            best_ask = min(orderBook.sell_orders.keys())
            best_ask_volume = orderBook.sell_orders[best_ask]
            volume = min(positionAdjustment, abs(best_ask_volume))
            print("Buying", volume, "at price", best_ask)

            return [Order(symbol, best_ask, volume)]
        else:
            best_bid = max(orderBook.buy_orders.keys())
            best_bid_volume = orderBook.buy_orders[best_bid]
            volume = min(positionAdjustment, -best_bid_volume)
            print("Selling", volume, "at price", best_bid)

            return [Order(symbol, best_bid, -volume)]

    def runPepper(
            self,
            state: TradingState,
            symbol: str,
            limit: int,
    ) -> list[Order] | None:
        '''
        Initial Strategy for IPR:

        Let fair price be modelled as:
        FP = slope * global_timestamp + intercept

        where slope = 0.00099992, intercept = 10000

        Consider z = (x - FP)/2.0008

        If z > 1.5 -> sell. Once z < 0.5 exit position and buy at that price.
        If z < -1.5 -> buy. Once z > -0.5 exit position and sell.
        '''
        orderBook = state.order_depths[symbol]
        position = state.position.get(symbol, 0)

        price = vwap(orderBook)

        if price is None:
            return None
        price = int(price)

        fairPrice = (0.00099992 * (state.timestamp + 3000000)) + 10000

        z = (price - fairPrice) / 2.0008

        if (self.pepperState == 0):
            if (z > 1.5):
                self.pepperState = 1
            elif (z < -1.5):
                self.pepperState = -1

        if (self.pepperState == 1):

            # Sell
            if (z > 1.5):
                bestBid = max(orderBook.buy_orders.keys())
                bestBidVolume = orderBook.buy_orders[bestBid]
                volume = min(abs(limit + position), abs(bestBidVolume))

                if (volume > 0):
                    return [Order(symbol, bestBid, -volume)]
                return None
            if (z > 0.5):
                return None

            # Exit the position, and buy at that price
            if (position < 0):
                bestAsk = min(orderBook.sell_orders.keys())
                bestAskVolume = orderBook.sell_orders[bestAsk]
                volume = min(abs(position), abs(bestAskVolume))

                if (volume > 0):
                    return [Order(symbol, bestAsk, volume)]
                return None

            # Reset state to neutral after all inventory cleared
            self.pepperState = 0

        if (self.pepperState == -1):

            # Buy
            if (z < -1.5):
                bestAsk = min(orderBook.sell_orders.keys())
                bestAskVolume = orderBook.sell_orders[bestAsk]
                volume = min(abs(position - limit), abs(bestAskVolume))

                if (volume > 0):
                    return [Order(symbol, bestAsk, volume)]
                return None

            if (z < -0.5):
                return None

            # Exit the position, and sell
            if (position > 0):
                bestBid = max(orderBook.buy_orders.keys())
                bestBidVolume = orderBook.buy_orders[bestBid]
                volume = min(abs(position), abs(bestBidVolume))

                if (volume > 0):
                    return [Order(symbol, bestBid, -volume)]
                return None

            # Reset state to neutral after all inventory cleared
            self.pepperState = 0

        return None


def vwap(order_depth: OrderDepth) -> float | None:
    '''
    Top-of-book VWAP with inverted volumes:
    (best_bid * ask_volume + best_ask * bid_volume) / (bid_volume + ask_volume).
    Returns None if either side of the book is empty.
    '''
    if (not order_depth.buy_orders) or (not order_depth.sell_orders):
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
    '''
    Halfway point between the highest bid and lowest ask.
    Returns None if either side of the book is empty.
    '''
    if not order_depth.buy_orders or not order_depth.sell_orders:
        return None

    best_bid = max(order_depth.buy_orders.keys())
    best_ask = min(order_depth.sell_orders.keys())

    return (best_bid + best_ask) / 2


def normalise_diff(price: float, average_price: float, deviation: float) -> float:
    '''
    Normalises the price to a value between -1 and 1, representing how far the
    price is from the average price in terms of standard deviations.
    '''
    return (price - average_price) / deviation


def bound_function1(diff: float) -> float:
    '''
    This function takes a price and returns a value between -1 and 1, representing the
    normalised position that should be taken based on the price.

    args:
        diff: A normalised difference between the average price and current price
    '''
    result = - (diff ** 3)
    if result > 1:
        return 1
    if result < -1:
        return -1
    return result


def bound_function2(diff: float) -> float:
    '''
    This function takes a price and returns a value between -1 and 1, representing the
    normalised position that should be taken based on the price.

    args:
        price: A normalised difference between the average price and current price
    '''
    result = - (math.cbrt(diff))
    if result > 1:
        return 1
    if result < -1:
        return -1
    return result


def calculate_adjustment(price: float, position: int, max_position: int) -> int:
    '''
    Calculates the position adjustment based on the price, current position, and maximum position.
    The adjustment is calculated by normalising the price, applying two bounding functions to determine the ideal

    args:
        price: The current price of the asset
        position: The current position in the asset
        max_position: The maximum allowed position in the asset
    '''
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


def bid_ask_spread(depth: OrderDepth) -> tuple[int, int] | None:
    if not depth.buy_orders or not depth.sell_orders:
        return None
    best_bid = max(depth.buy_orders.keys())
    best_ask = min(depth.sell_orders.keys())
    return (best_bid, best_ask)
