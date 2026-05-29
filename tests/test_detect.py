from seo_analyser.results.detect import extract_message_text, items_table, parse_response

OK_RESPONSE = {
    "status_code": 20000,
    "status_message": "Ok.",
    "cost": 0.002,
    "tasks": [
        {
            "status_code": 20000,
            "status_message": "Ok.",
            "cost": 0.002,
            "result": [
                {
                    "keyword": "shoes",
                    "location_code": 2826,
                    "items_count": 2,
                    "items": [
                        {"type": "organic", "rank_group": 1, "title": "A",
                         "domain": "a.com", "nested": {"x": 1}},
                        {"type": "organic", "rank_group": 2, "title": "B",
                         "domain": "b.com", "links": [1, 2]},
                    ],
                }
            ],
        }
    ],
}

TASK_ERROR_RESPONSE = {
    "status_code": 20000,
    "status_message": "Ok.",
    "cost": 0.0,
    "tasks": [
        {"status_code": 40501, "status_message": "Invalid Field.", "result": None}
    ],
}


def test_parse_ok():
    p = parse_response(OK_RESPONSE)
    assert p.ok is True
    assert p.cost == 0.002
    assert len(p.items) == 2
    assert p.result_meta["keyword"] == "shoes"


def test_parse_task_level_error():
    p = parse_response(TASK_ERROR_RESPONSE)
    assert p.ok is False
    assert "Invalid" in p.status_message
    assert p.items == []


def test_items_table_drops_nested():
    rows = items_table(parse_response(OK_RESPONSE).items)
    assert rows[0] == {"type": "organic", "rank_group": 1, "title": "A", "domain": "a.com"}
    assert "links" not in rows[1]


def test_parse_non_dict():
    p = parse_response("oops")
    assert p.ok is False


def test_extract_message_text_sections():
    items = [
        {"type": "reasoning"},
        {"type": "message", "sections": [{"type": "text", "text": "Salomon"},
                                          {"type": "text", "text": "Hoka"}]},
    ]
    assert extract_message_text(items) == "Salomon\n\nHoka"


def test_extract_message_text_plain_and_none():
    assert extract_message_text([{"text": "hello"}]) == "hello"
    assert extract_message_text([{"message": "hi"}]) == "hi"
    assert extract_message_text([{"type": "organic", "title": "x"}]) == ""
