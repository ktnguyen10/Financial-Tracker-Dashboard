class Budget:
    def __init__(self):
        self.categories = {}

    def add_new_category(self, new_cat, amount):
        # Check if numbers are strings or numbers when adding new category from site
        if isinstance(new_cat, str) and isinstance(amount, (int, float, complex)):
            self.categories[new_cat] = amount
        else:
            raise TypeError('The input cagtegory must be of str type, and the amount must be numeric or decimal.')

    def get_amount(self, cat):
        return self.categories[cat]

    def update_amount(self, cat, amount):
        if cat in self.categories.keys():
            self.categories[cat] = amount
        else:
            raise KeyError('No key named ' + cat + ' exists in current budget categories.')

    def remove_category(self):
        ...
