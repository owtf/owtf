"""Regression coverage for configuration placeholder expansion."""

from owtf.utils.strings import multi_replace


def test_empty_config_value_removes_its_placeholder():
    assert multi_replace("before@@@EMPTY@@@after", {"EMPTY": ""}) == "beforeafter"


def test_nested_empty_config_value_removes_its_placeholder():
    assert multi_replace("@@@A@@@", {"A": "prefix@@@B@@@suffix", "B": ""}) == "prefixsuffix"


def test_missing_config_value_keeps_its_placeholder():
    assert multi_replace("@@@MISSING@@@", {}) == "@@@MISSING@@@"
