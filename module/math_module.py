def add(x, y):
    """Returns the sum of x and y."""
    return x + y

def subtract(x, y):
    """Returns the difference of x and y."""
    return x - y

def multiply(x, y):
    """Returns the product of x and y."""
    return x * y

def divide(x, y):   
    """Returns the quotient of x and y. Raises ValueError if y is zero."""
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y
    