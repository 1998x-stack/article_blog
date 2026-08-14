from render import render_markdown


def test_renders_heading():
    html = render_markdown("# Hello")
    assert "<h1>Hello</h1>" in html


def test_strips_script():
    html = render_markdown("<script>alert(1)</script>")
    assert "script" not in html


def test_renders_code():
    html = render_markdown("```python\nprint(1)\n```")
    assert "<code" in html


def test_allows_safe_link():
    html = render_markdown("[ok](https://example.com)")
    assert 'href="https://example.com"' in html


def test_blocks_javascript_href():
    html = render_markdown("[x](javascript:alert(1))")
    assert "javascript:" not in html