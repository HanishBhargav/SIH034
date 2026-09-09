from backend.rules.rule_registry import get_rule, load_rule_registry


def test_rule_registry_loads_all_frozen_layers():
    registry = load_rule_registry()
    assert "APP_001" in registry
    assert "DECL_003" in registry


def test_rule_registry_returns_rule_definition():
    rule = get_rule("DECL_003")
    assert rule.rule_id == "DECL_003"
    assert rule.data["field"] == "commodity_name"
    assert rule.source["rule"] == "6"


def test_unknown_rule_id_raises_key_error():
    try:
        get_rule("DOES_NOT_EXIST")
    except KeyError as exc:
        assert "DOES_NOT_EXIST" in str(exc)
    else:
        raise AssertionError("Expected KeyError for unknown rule ID")
