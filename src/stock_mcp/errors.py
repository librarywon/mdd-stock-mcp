"""Custom error types for stock-mcp."""


class StockMCPError(Exception):
    """Base error for all stock-mcp errors."""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class InvalidTickerError(StockMCPError):
    """Raised when a ticker symbol is not found or returns no data."""

    def __init__(self, ticker: str, message: str = ""):
        self.ticker = ticker
        if not message:
            message = f"Ticker '{ticker}' not found or returned no data from Yahoo Finance."
        super().__init__(message)


class NoDataError(StockMCPError):
    """Raised when a valid ticker returns no usable data for the requested range."""

    def __init__(self, ticker: str = "", message: str = ""):
        self.ticker = ticker
        if not message:
            message = f"No data available for ticker '{ticker}' in the requested date range."
        super().__init__(message)


class InvalidDateError(StockMCPError):
    """Raised when a date is malformed or out of allowed range."""

    def __init__(self, message: str = ""):
        super().__init__(message)
