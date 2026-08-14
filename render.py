import markdown as _md
import bleach

_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "strong", "em", "del", "code", "pre", "blockquote",
    "a", "ul", "ol", "li", "img", "table", "thead", "tbody",
    "tr", "th", "td",
]
_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}
_ALLOWED_PROTOCOLS = {"http", "https", "mailto"}


def render_markdown(text: str) -> str:
    processor = _md.Markdown(extensions=["fenced_code", "tables", "nl2br", "sane_lists"])
    html = processor.convert(text or "")
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )