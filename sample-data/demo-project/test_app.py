from app import greeting


def test_greeting_has_exclamation_mark():
    assert greeting("Ada") == "Hello, Ada!"
