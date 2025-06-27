EXTENSION_GROUPS = {
    "Text Files": [
        ".txt", ".md", ".asc", ".dok", ".text", ".rtf", ".rst", ".tex",
    ],
    "Data Files": [
        ".csv", ".log", ".xlog", ".lst", ".tsv", ".json", ".xml", ".yml",
        ".yaml", ".ini",
    ],
    "Code Files": [
        ".py", ".cs", ".rs", ".html", ".htm", ".js", ".ts", ".c", ".cpp",
        ".java", ".bat", ".sh", ".ps1", ".css", ".go", ".rb", ".php",
    ],
}

DEFAULT_EXTENSION_CATEGORIES = ["Text Files", "Code Files"]


def parse_categories(text: str) -> list[str]:
    return [c.strip() for c in text.split(',') if c.strip()]


def build_extension_filters(categories: list[str], allow_all: bool) -> list[str]:
    if allow_all:
        return []
    exts: list[str] = []
    for name in categories:
        exts.extend(EXTENSION_GROUPS.get(name, []))
    return sorted(set(exts))

