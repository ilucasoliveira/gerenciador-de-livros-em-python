import pytest

def soma(a: int | float, b: int | float) -> float:
    return round(a + b, 2)

def test_soma():
    assert soma(12, 15.55) == 27.55
    assert soma(3, 3) == 6
    assert soma(0, 10) == 10
    assert soma(10, -1) == 9
    assert soma(-1, -1) == -2