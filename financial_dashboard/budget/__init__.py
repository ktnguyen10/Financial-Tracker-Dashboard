class Budget:
    def __init__(self):
        self.categories = {}

    def add_new_category(self, new_cat, amount):
        # Check if numbers are strings or numbers when adding new category from site
        if isinstance(new_cat, str) and isinstance(amount, (int, float, complex)):
            self.categories[new_cat] = amount
        else:
            raise TypeError('The input category must be of str type, and the amount must be numeric or decimal.')

    @staticmethod
    def get_budget(curs, username):
        curs.execute("SELECT * FROM budgets WHERE username LIKE (?)", (username,))
        budget = curs.fetchall()
        if budget:
            return dict(zip(budget['category'], budget['amount']))
        else:
            return {'No Budget': 0}

    def get_amount(self, cat):
        return self.categories[cat]

    def update_amount(self, curs, conn, username, cat, amount):
        if cat in self.categories.keys():
            self.categories[cat] = amount
            # Insert user information into users table with initial cash value of 10000
            curs.execute(
                "INSERT INTO budgets (username, cat, amount) VALUES(?, ?, ?)",
                (username, cat, amount)
            )
        else:
            self.add_new_category(cat, amount)
            curs.execute(
                "UPDATE budgets SET username=(username), category=(cat), amount=(amount)  VALUES(?, ?, ?)",
                (username, cat, amount)
            )
        conn.commit()


    def remove_category(self):
        ...
