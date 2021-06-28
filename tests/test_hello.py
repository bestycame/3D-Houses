from becode3d.hello import print_hello

def test_hello_returns_correct_test():
    assert print_hello() == 'Hello World'

def test_tests():
    assert 'OK' is 'OK'