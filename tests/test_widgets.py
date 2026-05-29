from typing import List, Optional

from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr

from seo_analyser.forms.widgets import FieldSpec, extract_choices, extract_range, fields_for


class _Sample(BaseModel):
    keyword: Optional[StrictStr] = Field(default=None, description="keyword required field")
    depth: Optional[StrictInt] = Field(default=None, description="parsing depth, max value: 200")
    device: Optional[StrictStr] = Field(default=None, description="possible values: desktop, mobile")
    group: Optional[StrictBool] = Field(default=True, description="default value: true")
    keywords: Optional[List[StrictStr]] = Field(default=None, description="list of keywords")


def test_extract_choices():
    assert extract_choices("possible values: desktop, mobile") == ["desktop", "mobile"]
    assert extract_choices("no enum here") == []


def test_extract_range():
    assert extract_range("parsing depth, max value: 200") == (None, 200)
    assert extract_range("range: 240-9999") == (240, 9999)
    assert extract_range("possible values from 1 to 4") == (1, 4)
    assert extract_range("no range") == (None, None)


def test_fields_for_kinds():
    specs = {f.name: f for f in fields_for(_Sample)}
    assert specs["keyword"].kind == "text"
    assert specs["depth"].kind == "int"
    assert specs["depth"].max == 200
    assert specs["device"].kind == "select"
    assert specs["device"].choices == ["desktop", "mobile"]
    assert specs["group"].kind == "bool"
    assert specs["group"].default is True
    assert specs["keywords"].kind == "list"


def test_fieldspec_carries_description():
    specs = {f.name: f for f in fields_for(_Sample)}
    assert "required" in specs["keyword"].description
