def mul(x, y):
    """Returns the product of x and y."""
    return x * y

def div(x, y):
    """Returns the quotient of x and y. Raises ValueError if y is zero."""
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y