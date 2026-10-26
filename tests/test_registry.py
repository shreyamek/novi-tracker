from novi import registry


def test_register_feature_listed_in_order():
    registry.clear()
    registry.register("a", {}, {"label": "A"})
    registry.register("b", {}, {"label": "B"})
    assert [f["name"] for f in registry.features()] == ["a", "b"]
    assert registry.features()[0]["tab"] == {"label": "A"}
