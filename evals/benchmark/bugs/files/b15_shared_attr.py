class Cart:
    items = []          # bug: class attribute shared across all instances
    def add(self, x):
        self.items.append(x)
