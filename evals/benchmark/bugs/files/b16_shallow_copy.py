def with_item(order, item):
    new = order.copy()          # shallow: nested 'lines' still shared
    new['lines'].append(item)
    return new
