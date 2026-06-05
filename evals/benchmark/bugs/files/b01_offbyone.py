def sum_prices(prices):
    total = 0
    for i in range(len(prices) + 1):
        total += prices[i]
    return total
