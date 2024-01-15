from forex_python.converter import CurrencyRates


def currency_converter(from_currency, to_currency, amount):
    cr = CurrencyRates()
    output = cr.convert(from_currency, to_currency, amount)
    return output
