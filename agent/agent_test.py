# Agent test module
print("Original test file")


def hello():
    return "Hello from AI Agent"


def greet():
    return "Hello from Agent"


def test_greet():
    assert greet() == "Hello from Agent"
