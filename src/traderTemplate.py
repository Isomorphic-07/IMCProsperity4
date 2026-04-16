from abc import ABC, abstractmethod
from src.library.datamodel import *

class Trader(ABC):
    @abstractmethod
    def run(self, state: TradingState) -> tuple[dict, int, str]:
        pass

    