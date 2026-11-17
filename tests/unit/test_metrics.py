import pytest

from app.evaluation import faithfulness, hit_at_k, recall_at_k


def test_recall():
    assert recall_at_k(["a", "b"], ["a", "x", "y"], 3) == 0.5
    assert hit_at_k(["a"], ["x"], 5) == 0.0

def test_faithfulness():
    assert faithfulness(3, 4) == 0.75
    with pytest.raises(ValueError):
        faithfulness(2, 1)
