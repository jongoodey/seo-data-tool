from seo_analyser.results.detect import (
    extract_html, extract_links, extract_message_text, items_table, looks_like_html,
    parse_response, sanitize_for_preview, strip_scripts,
)

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


_PAGE = ("<html><head><title>Test page here</title></head>"
         "<body><h1>Heading</h1><p>Some paragraph text.</p></body></html>")


def test_looks_like_html():
    assert looks_like_html(_PAGE) is True
    assert looks_like_html("just a sentence, not html") is False
    assert looks_like_html("<p>only one tag, far too short to count</p>") is False


def test_extract_html_finds_nested_largest():
    resp = {"tasks": [{"result": [{"items": [
        {"html": _PAGE},
        {"snippet": "<b>x</b>"},
    ]}]}]}
    html = extract_html(resp)
    assert html is not None and "<h1>Heading</h1>" in html


def test_extract_html_none_when_absent():
    assert extract_html({"tasks": [{"result": [{"keyword": "shoes"}]}]}) is None


def test_strip_scripts():
    html = '<html><body><h1>Hi</h1><script>location.href="/x"</script><p>ok</p></body></html>'
    out = strip_scripts(html)
    assert "<script" not in out
    assert "location.href" not in out
    assert "<h1>Hi</h1>" in out and "<p>ok</p>" in out


def test_sanitize_for_preview_disables_links_and_scripts():
    out = sanitize_for_preview('<a href="/x">link</a><script>alert(1)</script>')
    assert "pointer-events:none" in out
    assert "<script" not in out
    assert "link" in out  # link text kept, just non-clickable


def test_extract_links_from_annotations():
    items = [{"type": "message", "sections": [{"type": "text", "text": "answer",
              "annotations": [
                  {"title": "REI", "url": "https://rei.com"},
                  {"title": "RunRepeat", "url": "https://runrepeat.com"},
                  {"title": "REI dup", "url": "https://rei.com"},  # dup url
              ]}]}]
    links = extract_links(items)
    assert links == [
        {"title": "REI", "url": "https://rei.com"},
        {"title": "RunRepeat", "url": "https://runrepeat.com"},
    ]


def test_extract_links_none():
    assert extract_links([{"type": "message", "sections": [{"text": "hi"}]}]) == []


def test_extract_message_text_plain_and_none():
    assert extract_message_text([{"text": "hello"}]) == "hello"
    assert extract_message_text([{"message": "hi"}]) == "hi"
    assert extract_message_text([{"type": "organic", "title": "x"}]) == ""
