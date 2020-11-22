from Discord_Stonks.stocks.stocks import validateTicker


class TestStockController:

    real_stock_tickers = ['AAPL', 'AMZN', 'MSFT', 'SPY', 'ESTC']
    fake_stock_tickers = ['TVIX', '3M', 'AMZNN', 'AAPLS']

    def test_validateTicker(self):
        for stock in self.real_stock_tickers:
            validate = validateTicker(stock)
            assert validate

        for fake_stock in self.fake_stock_tickers:
            validate = validateTicker(fake_stock)
            assert validate
