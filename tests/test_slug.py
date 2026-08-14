from slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_punctuation():
    assert slugify("C# & Python!") == "c-python"


def test_unicode():
    assert slugify("Café") == "cafe"


def test_empty():
    assert slugify("  ") == "untitled"