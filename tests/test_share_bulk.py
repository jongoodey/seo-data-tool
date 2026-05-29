from seo_analyser.runner.bulk import MAX_ROWS, rows_to_payloads
from seo_analyser.ui.share import decode_share, encode_share


def test_share_roundtrip():
    token = encode_share("serp", "google_organic_live_advanced",
                         {"keyword": "shoes", "location_code": 2826})
    out = decode_share(token)
    assert out == {
        "family": "serp",
        "endpoint": "google_organic_live_advanced",
        "params": {"keyword": "shoes", "location_code": 2826},
    }


def test_decode_invalid():
    assert decode_share("not-base64!!") is None
    assert decode_share("") is None


def test_rows_to_payloads():
    payloads = rows_to_payloads({"location_name": "UK"}, "keyword", ["a", "", "b"])
    assert payloads == [
        {"location_name": "UK", "keyword": "a"},
        {"location_name": "UK", "keyword": "b"},
    ]


def test_rows_to_payloads_capped():
    payloads = rows_to_payloads({}, "keyword", [str(i) for i in range(100)])
    assert len(payloads) == MAX_ROWS
