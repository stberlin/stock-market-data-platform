from src.api.stock_api import get_stock_data_time_series


data = get_stock_data_time_series("AAPL")

print(data[:1])