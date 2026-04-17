from src.library.datamodel import (
    Listing,
    ConversionObservation,
    Observation, Order,
    OrderDepth, Trade,
    TradingState,
    ProsperityEncoder
)

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
        pass

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
        pass