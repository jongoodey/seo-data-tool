from typing import List, Optional

from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr

from seo_analyser.forms.widgets import (
    FieldSpec,
    extract_choices,
    extract_default,
    extract_range,
    extract_requirement,
    fields_for,
    resolve_partner,
)


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


def test_extract_requirement():
    assert extract_requirement("keywordsrequired fieldUTF-8") == "required"
    assert extract_requirement("full name of the languageoptional field") == "optional"
    assert extract_requirement(
        "required field if you don't specify location_code") == "conditional"
    assert extract_requirement("no hints here") == ""


def test_resolve_partner_against_siblings():
    # Space-less description: 'language_codeif' must still resolve to language_code.
    desc = "required field if you don't specify language_codeif you use this field"
    assert resolve_partner(desc, ["language_name", "language_code", "keywords"]) == "language_code"
    assert resolve_partner("no clause", ["a", "b"]) is None


def test_extract_default():
    assert extract_default("group results default value: true here") == "true"
    assert extract_default("no default") is None


def test_additional_properties_excluded():
    class _WithCatchAll(BaseModel):
        keyword: Optional[StrictStr] = Field(default=None)
        additional_properties: Optional[StrictStr] = Field(default=None)

    names = [f.name for f in fields_for(_WithCatchAll)]
    assert "keyword" in names
    assert "additional_properties" not in names


def test_dict_fields_get_dict_kind():
    from typing import Dict
    class _WithDict(BaseModel):
        targets: Optional[Dict[str, Optional[str]]] = Field(default=None)
        keyword: Optional[StrictStr] = Field(default=None)

    kinds = {f.name: f.kind for f in fields_for(_WithDict)}
    assert kinds["targets"] == "dict"
    assert kinds["keyword"] == "text"


def test_real_intersection_targets_is_dict_kind():
    from seo_analyser.registry.introspect import build_catalogue
    inter = next(e for e in build_catalogue()["backlinks"]
                 if e.name == "domain_intersection_live")
    kinds = {f.name: f.kind for f in fields_for(inter.request_model)}
    assert kinds["targets"] == "dict"


def test_requirement_polarity_dont_specify_vs_choose_to_specify():
    from seo_analyser.forms.widgets import extract_requirement
    assert extract_requirement(
        "required field if you don't specify location_code") == "conditional"
    assert extract_requirement(
        "required field if you choose to specify custom_mode") == "dependent"
    assert extract_requirement(
        "required field if you specify custom_mode") == "dependent"
    assert extract_requirement("required field") == "required"
    assert extract_requirement("optional field") == "optional"


def test_backlinks_live_field_value_classified_dependent():
    from seo_analyser.registry import catalogue
    from seo_analyser.forms.widgets import fields_for
    meta = catalogue.find_endpoint("backlinks", "backlinks_live")
    by_name = {s.name: s for s in fields_for(meta.request_model)}
    assert by_name["field"].requirement == "dependent"
    assert by_name["field"].partner == "custom_mode"
    assert by_name["value"].requirement == "dependent"
    assert by_name["target"].requirement == "required"
