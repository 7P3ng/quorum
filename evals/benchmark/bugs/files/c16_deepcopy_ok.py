import copy


def with_item(order, item):
    new = copy.deepcopy(order)
    new['lines'].append(item)
    return new
