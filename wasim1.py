import os
import sys  # unused import (style issue)

class MathOps:
    def __init__(self):
        self.value = 10

    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        return a / b   # ⚠️ runtime error if b == 0

# Function with syntax error
def broken_function(    # ❌ Syntax error (missing closing parenthesis)
    print("This line is broken")

# Function with bad naming and unused variable
def BADfunction(x, y):   # ❌ Naming convention issue
    temp = 123           # unused variable
    return x * y

# Indentation error
def wrong_indent():
print("This will cause IndentationError")  # ❌ wrong indent

# Unreachable code
def check_number(n):
    return True
    print("This will never run")  # ❌ unreachable

# Main block
if __name__ == "__main__":
    math = MathOps()
    print(math.add(5, 3))
    print(math.divide(10, 0))   # ❌ ZeroDivisionError
