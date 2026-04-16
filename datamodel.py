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


class Listing:

    def __init__(self, symbol: Symbol, product: Product, denomination: Product):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination


class ConversionObservation:

    def __init__(
            self,
            bidPrice: float,
            askPrice: float,
            transportFees: float,
            exportTariff: float,
            importTariff: float,
            sunlight: float,
            humidity: float
    ):

        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sugarPrice = sugarPrice
        self.sunlightIndex = sunlightIndex

class Observation:

    def __init__(
            self,
            plainValueObservations: Dict[Product, ObservationValue],
            conversionObservations: Dict[Product, ConversionObservation]
    ) -> None:

        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations

    def __str__(self) -> str:
        return "(plainValueObservations: " + jsonpickle.encode(self.plainValueObservations) + ", conversionObservations: " + jsonpickle.encode(self.conversionObservations) + ")"


class Order:

    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"


class OrderDepth:

    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}

    def sort_buys(self):
        '''
        Obviously, the best buy orders are the ones with the highest price,
        so we want to sort them in decreasing order of price.
        '''
        self.buy_orders = dict(
            sorted(self.buy_orders.items(),
            key=lambda item: item[0],
            reverse=True)
        )

    def sort_sells(self):
        '''
        The best sell orders are the ones with the lowest price,
        so we want to sort them in increasing order of price.
        '''
        self.sell_orders = dict(
            sorted(self.sell_orders.items(),
            key=lambda item: item[0])
        )


class Trade:

    def __init__(
            self,
            symbol: Symbol,
            price: int,
            quantity: int,
            buyer: UserId=None,
            seller: UserId=None,
            timestamp: int=0
        ) -> None:

        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + self.buyer + " << " + self.seller + ", " + str(self.price) + ", " + str(self.quantity) + ", " + str(self.timestamp) + ")"

    def get_buyer(self) -> UserId:
        return self.buyer

    def get_seller(self) -> UserId:
        return self.seller

class TradingState(object):

    def __init__(self,
                 traderData: str,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings

        # All the buy and sell orders per product that other market participants have sent
        # and that the algorithm is able to trade with. This property is a dict where the
        # keys are the products and the corresponding values are instances of the OrderDepth class.
        # This OrderDepth class then contains all the buy and sell orders.
        self.order_depths = order_depths

        # The trades the algorithm itself has done since the last TradingState came in.
        # This property is a dictionary of Trade objects with key being a product name.
        # The definition of the Trade class is provided in the subsections below.
        self.own_trades = own_trades

        # The trades that other market participants have done since the last TradingState came in.
        # This property is also a dictionary of Trade objects with key being a product name.
        self.market_trades = market_trades

        # The long or short position that the player holds in every tradable product.
        # This property is a dictionary with the product as the key for which the value is
        # a signed integer denoting the position, e.g. {product1: 2, product2: -1}.
        self.position = position

        self.observations = observations

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class ProsperityEncoder(JSONEncoder):

        def default(self, o):
            return o.__dict__
