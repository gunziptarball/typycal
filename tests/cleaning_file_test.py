"""
Example: Transforming a CSV to include formatting
"""
import pytest

csv_file = """
item,cost
banana,3
apple,$2
sausage,9.6
""".strip()

expected_result = """
item,cost
banana,$3.00
apple,$2.00
sausage,$9.60
""".strip()

import typycal
import re

p = re.compile(r'(?P<item>.+),\$?(?P<cost>[0-9.]+)')


@typycal.typed_str(r'(?P<item>[^,]+),\$?(?P<cost>[0-9.]+)', template='{item},${cost:.2f}')
class Fruit(str):
    item: str
    cost: float


def convert_text(text_in):
    return '\n'.join(typycal.transform_lines(Fruit, text_in.split('\n')))


def test_conversion():
    assert expected_result == convert_text(csv_file)
    assert expected_result == '\n'.join(typycal.transform_lines(Fruit, csv_file))
    with pytest.raises(ValueError):
        list(typycal.transform_lines(Fruit, csv_file, strict=True))
