import re
import unicodedata


def slugify(title):
    s = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"