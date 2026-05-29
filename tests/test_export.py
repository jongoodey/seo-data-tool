import json

from seo_analyser.results.export import to_csv_bytes, to_json_bytes


def test_to_csv_bytes_has_header_and_rows():
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    text = to_csv_bytes(rows).decode("utf-8")
    assert "a,b" in text.splitlines()[0]
    assert "1,x" in text


def test_to_csv_empty():
    assert to_csv_bytes([]) == b""


def test_to_csv_unions_columns():
    rows = [{"a": 1}, {"b": 2}]
    header = to_csv_bytes(rows).decode("utf-8").splitlines()[0]
    assert "a" in header and "b" in header


def test_to_json_bytes_roundtrips():
    payload = {"status_code": 20000, "tasks": [{"id": "1"}]}
    assert json.loads(to_json_bytes(payload)) == payload
