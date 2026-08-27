
from engineering.app.universal_quality import _finite_tree


def test_finite_tree_accepts_engineering_numbers():
    assert _finite_tree({"sigma": 0.12, "values": [1, 2, 3]})


def test_finite_tree_rejects_nan_and_infinity():
    assert not _finite_tree({"value": float("nan")})
    assert not _finite_tree({"value": float("inf")})


def test_quality_constants_are_bounded():
    from engineering.app.universal_quality import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES
    assert 1_000_000 <= MAX_REQUEST_BYTES <= 100_000_000
    assert 1_000_000 <= MAX_RESPONSE_BYTES <= 100_000_000
