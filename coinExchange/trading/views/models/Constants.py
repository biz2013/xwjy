from enum import Enum

class OrderSource(Enum):
  TradingSite = 'TRADESITE'
  ThirdPartyAPI = 'ThirdPartyAPI'
  AxFundTradingSite = 'AxFundTradingSite'
