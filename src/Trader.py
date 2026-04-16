from src.datamodel import (
    Listing,
    ConversionObservation,
    Observation, Order,
    OrderDepth, Trade,
    TradingState,
    ProsperityEncoder
)

import json
from typing import Dict, List
from json import JSONEncoder
import jsonpickle

Time = int
Symbol = str
Product = str
Position = int
UserId = str
ObservationValue = int

ashCoatedOsmiumLimit = 80  # ASH_COATED_OSMIUM
intarianPepperRootLimit = 80  # INTARIAN_PEPPER_ROOT

BUY = 1
SELL = -1


class Trader:
    def __init__(self) -> None:
        self.ashCoatedOsmiumPosition = 0
        self.intarianPepperRootPosition = 0

    # This is the main function called every round, where the logic for
    # our algorithm will be impemented.
    def run(self, state: TradingState):

        # Handle logic for ASH_COATED_OSMIUM
        # ----------------------------------
        '''look at z = (x - 10000)/5.35, if z > 2, we are gonna sell, once
        z < 0.5 we exit this position and buy the instrument at that price
        For the other direction, if z < -2, we are gonna buy, then track the price
        if the price goes z >= -0.5, we exit this position and sell.
        '''
        # Orders to be placed on exchange matching engine
        result = {"ASH_COATED_OSMIUM": [], "INTARIAN_PEPPER_ROOT": []}

        ashOrders = state.order_depths["ASH_COATED_OSMIUM"]
        ashOrders = self.sort_buys(ashOrders)
        ashOrders = self.sort_sells(ashOrders)

        acceptablePrice = self.calculate_fair_price(ashOrders)

        orders: List[Order] = []
        print("Acceptable price : " + str(acceptablePrice))
        print("Buy Order depth : " + str(len(ashOrders.buy_orders)) + ", Sell order depth : " + str(len(ashOrders.sell_orders)))

        if len(ashOrders.sell_orders) != 0:

            # We are going to buy
            if (acceptablePrice < 9989):
                bestAsk = ashOrders.buy_orders.keys()[0]
                bestAskAmount = ashOrders.buy_orders[bestAsk]
                print("BUY", str(-bestAskAmount) + "x", bestAsk)

                # Confirm this order logic
                orders.append(Order("ASH_COATED_OSMIUM", bestAsk, -bestAskAmount))

        if len(ashOrders.buy_orders) != 0:

            # We are going to sell
            if (acceptablePrice > 10011):
                bestBid = ashOrders.buy_orders.keys()[0]
                bestBidAmount = ashOrders.buy_orders[bestBid]
                print("SELL", str(bestBidAmount) + "x", bestBid)

                # Confirm this order logic
                orders.append(Order("ASH_COATED_OSMIUM", bestBid, -bestBidAmount))

        result["ASH_COATED_OSMIUM"] = orders

        traderData = ""  # No state needed - we check position directly
        conversions = 0

        # Handle logic for INTARIAN_PEPPER_ROOT
        # -------------------------------------

        return result, conversions, traderData

    # Ignore this class for now, only required for Round 2 and beyond.
    def bid(self):
        pass

    # Ignore our own trades, only consider trades from other traders.
    def is_own_trade(self, trade: Trade) -> bool:
        return (trade.get_buyer() == "SUBMISSION") or (trade.get_seller() == "SUBMISSION")

    def get_max_position(self, symbol: str, direction: int) -> int:

        # Confirm direction is valid
        if (direction != BUY and direction != SELL):
            raise ValueError("Direction must be either BUY or SELL")

        # Confirm symbol is valid
        if (symbol != "ASH_COATED_OSMIUM" and symbol != "INTARIAN_PEPPER_ROOT"):
            raise ValueError("Unknown symbol: " + symbol)

        if (symbol == "ASH_COATED_OSMIUM"):
            return ashCoatedOsmiumLimit - (
                direction * self.ashCoatedOsmiumPosition
            )

        if (symbol == "INTARIAN_PEPPER_ROOT"):
            return intarianPepperRootLimit - (
                direction * self.intarianPepperRootPosition
            )

    def calculate_fair_price(self, order_depth: OrderDepth) -> int:
        '''
        Could just take the mid price, from the best buy and sell orders.
        But if there are more orders on one side, we might want to weight
        the price more towards that side.
        '''
        midPrice = (order_depth.sell_orders.keys()[0] + order_depth.buy_orders.keys()[0]) / 2
        return midPrice
