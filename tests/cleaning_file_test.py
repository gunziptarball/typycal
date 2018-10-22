"""
Example: Transforming a CSV to include formatting
"""
import pytest

CSV_FILE = """
item,cost
banana,3
apple,$2
sausage,9.6
""".strip()

EXPECTED_RESULT = """
item,cost
banana,$3.00
apple,$2.00
sausage,$9.60
""".strip()

import typycal
import re

@typycal.typed_str(r'(?P<item>[^,]+),\$?(?P<cost>[0-9.]+)', template='{item},${cost:.2f}')
class Fruit(str):
    item: str
    cost: float


def convert_text(text_in):
    return '\n'.join(typycal.transform_lines(Fruit, text_in.split('\n')))


def test_conversion():
    assert EXPECTED_RESULT == convert_text(CSV_FILE)
    assert EXPECTED_RESULT == '\n'.join(typycal.transform_lines(Fruit, CSV_FILE))
    with pytest.raises(ValueError):
        list(typycal.transform_lines(Fruit, CSV_FILE, strict=True))
