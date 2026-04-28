class Person:
    # pass
    def __init__(self, name):
        self.name = name

    def hello(self):
        print(f"Hello, I'm {self.name}!")
    
    def update_age(self, age):
        if age < 0:
            raise ValueError("Age cannot be negative.")
        else:
            self.age = age
            print(f"Age updated to {self.age}"
                )
if __name__ == "__main__":
    man = Person("John")
    man.hello()
    man.update_age(30)
