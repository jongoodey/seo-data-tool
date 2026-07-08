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


# --- friendly_error -----------------------------------------------------------

def test_friendly_error_translates_invalid_field():
    from seo_analyser.results.detect import friendly_error
    msg = friendly_error("Invalid Field: 'keyword'.", 40501)
    assert "keyword" in msg
    assert "fill in" in msg.lower() or "missing" in msg.lower()
    assert "Invalid Field" in msg  # original preserved for power users


def test_friendly_error_translates_task_not_found():
    from seo_analyser.results.detect import friendly_error
    msg = friendly_error("Task Not Found.", 40401)
    assert "still be processing" in msg


def test_friendly_error_passes_through_unknown():
    from seo_analyser.results.detect import friendly_error
    assert friendly_error("You have reached your limit.", 40202) == "You have reached your limit."


# --- AI Overview / AI Mode shapes (markdown answers + references) -------------

def test_extract_message_text_falls_back_to_markdown():
    from seo_analyser.results.detect import extract_message_text
    items = [{"type": "ai_overview", "markdown": "**Best shoes** are...", "xpath": "/div[1]"}]
    assert extract_message_text(items) == "**Best shoes** are..."


def test_sections_text_preferred_over_markdown():
    from seo_analyser.results.detect import extract_message_text
    items = [{"sections": [{"text": "from sections"}], "markdown": "from markdown"}]
    assert extract_message_text(items) == "from sections"


def test_extract_links_collects_references():
    from seo_analyser.results.detect import extract_links
    items = [{
        "type": "ai_overview",
        "references": [{"title": "Best 2026 shoes", "url": "https://a.com/x"}],
        "items": [{"type": "ai_overview_element",
                   "references": [{"title": "Nested ref", "url": "https://b.com/y"},
                                  {"title": "Dup", "url": "https://a.com/x"}]}],
    }]
    links = extract_links(items)
    assert {l["url"] for l in links} == {"https://a.com/x", "https://b.com/y"}


def test_items_table_drops_machine_noise_columns():
    from seo_analyser.results.detect import items_table
    rows = items_table([{"title": "t", "xpath": "/div[1]/div[2]", "rank_group": 1}])
    assert rows == [{"title": "t", "rank_group": 1}]


# --- extract_time_series (timeline charts) --------------------------------------

def _envelope(item):
    return {"status_code": 20000, "tasks": [{"status_code": 20000,
            "result": [{"items": [item]}]}]}


def test_ai_keyword_volume_monthly_series_detected():
    # The exact shape from ai_keyword_data_keywords_search_volume_live.
    from seo_analyser.results.detect import extract_time_series
    item = {"keyword": "best running shoes",
            "ai_monthly_searches": [
                {"year": 2026, "month": 1, "ai_search_volume": 4486},
                {"year": 2025, "month": 12, "ai_search_volume": 4766},
                {"year": 2025, "month": 11, "ai_search_volume": 4170},
            ]}
    series = extract_time_series(_envelope(item))
    assert len(series) == 1
    s = series[0]
    assert s["label"] == "best running shoes · ai_search_volume"
    assert s["points"][0] == ("2025-11-01", 4170.0)   # sorted chronologically
    assert s["points"][-1] == ("2026-01-01", 4486.0)


def test_google_ads_monthly_searches_detected():
    from seo_analyser.results.detect import extract_time_series
    item = {"keyword": "cashmere jumper",
            "monthly_searches": [
                {"year": 2026, "month": m, "search_volume": 1000 + m} for m in (1, 2, 3, 4)
            ]}
    series = extract_time_series(_envelope(item))
    assert series and series[0]["label"] == "cashmere jumper · search_volume"
    assert len(series[0]["points"]) == 4


def test_dated_timeseries_rows_detected():
    # backlinks timeseries shape: date string + several numeric metrics.
    from seo_analyser.results.detect import extract_time_series
    rows = [{"date": f"2026-0{m}-01 00:00:00 +00:00", "backlinks": 100 * m,
             "referring_domains": 10 * m} for m in (1, 2, 3)]
    series = extract_time_series({"tasks": [{"result": [{"items": rows}]}]})
    labels = {s["label"] for s in series}
    assert labels == {"backlinks", "referring_domains"}
    assert series[0]["points"][0][0] == "2026-01-01"


def test_non_series_rows_ignored():
    from seo_analyser.results.detect import extract_time_series
    serp_rows = [{"rank_group": i, "title": f"r{i}", "url": "https://x"} for i in range(10)]
    assert extract_time_series({"tasks": [{"result": [{"items": serp_rows}]}]}) == []


def test_series_capped_and_two_point_series_skipped():
    from seo_analyser.results.detect import extract_time_series
    item = {"keyword": "k",
            "short": [{"year": 2026, "month": 1, "v": 1}, {"year": 2026, "month": 2, "v": 2}]}
    assert extract_time_series(_envelope(item)) == []
