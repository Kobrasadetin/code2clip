EXTENSION_GROUP_DEFAULTS = {
    "Text Files": [
        ".txt",
        ".md",
        ".asc",
        ".dok",
        ".text",
        ".rtf",
        ".rst",
        ".tex",
    ],
    "Data Files": [
        ".csv",
        ".log",
        ".xlog",
        ".lst",
        ".tsv",
        ".json",
        ".xml",
        ".yml",
        ".yaml",
        ".ini",
    ],
    "Code Files": [
        ".py",
        ".cs",
        ".rs",
        ".html",
        ".htm",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".mjs",
        ".c",
        ".cpp",
        ".java",
        ".bat",
        ".sh",
        ".ps1",
        ".css",
        ".go",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".kts",
        ".lua",
        ".pl",
        ".sql",
        ".vb",
    ],
}

DEFAULT_EXTENSION_CATEGORIES = ["Text Files", "Code Files"]


def parse_categories(text: str) -> list[str]:
    return [c.strip() for c in text.split(",") if c.strip()]


def parse_extensions(text: str) -> list[str]:
    exts: list[str] = []
    for item in text.split(","):
        ext = item.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        exts.append(ext)
    return exts


def build_extension_filters(
    categories: list[str], allow_all: bool, groups: dict[str, list[str]]
) -> list[str]:
    if allow_all:
        return []
    exts: list[str] = []
    for name in categories:
        exts.extend(groups.get(name, []))
    return sorted(set(exts))

