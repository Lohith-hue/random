def add (a,b):
    return a + b

def substract(a,b):
    return a - b

def multiply(a,b):
    return a * b

def divide(a,b):
    return a / b

print(f"let's do some math with just functions!")

addition = add(30,5)
print(f"value of addition = {addition} and type = {type(addition)}")
substraction = substract(78,4)
print(f"value of substraction = {substraction} and type = {type(substraction)}")
multiplications = multiply(90,2)
print(f"value of multiplication = {multiplications} and type = {type(multiplications)}")
division = divide(100,2)
print(f"value of division = {division} and type = {type(division)}")
# A puzzle for extra credit type it in anyway.

what = add(addition, substract(substraction, multiply(multiplications, divide(division,2))))

print(f"That becomes: {what} can you do it by hand?")
