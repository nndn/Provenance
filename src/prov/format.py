"""TTY-aware ANSI formatting and box-drawing. Stdlib only."""
import sys

# ANSI escape sequences
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _is_tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def t(text: str, *styles: str) -> str:
    """Apply ANSI styles to text only when stdout is a TTY."""
    if not _is_tty():
        return text
    if not styles:
        return text
    codes = "".join(s for s in styles if s in (BOLD, DIM, CYAN, GREEN, YELLOW))
    return f"{codes}{text}{RESET}"


def rule(char: str = "─", width: int = 60) -> str:
    """Return a horizontal rule of given width."""
    return char * min(width, 80)


def box_header(text: str, width: int = 44) -> str:
    """Return a boxed header (top, content, bottom)."""
    inner = text[: width - 4].ljust(width - 4)
    lines = [
        "╔" + "═" * (width - 2) + "╗",
        f"║ {inner}║",
        "╚" + "═" * (width - 2) + "╝",
    ]
    return "\n".join(lines)


# Domain table column widths: (label, content_width)
DOMAIN_COLS = [
    ("Domain", 12),
    ("Summary", 26),
    ("Reqs", 5),
    ("Planned", 8),
    ("Qs", 4),
    ("Assumptions", 11),
]


def _table_top(cols: list[tuple[str, int]]) -> str:
    return "┌" + "┬".join("─" * (w + 2) for _, w in cols) + "┐"


def _table_sep(cols: list[tuple[str, int]]) -> str:
    return "├" + "┼".join("─" * (w + 2) for _, w in cols) + "┤"


def _table_bottom(cols: list[tuple[str, int]]) -> str:
    return "└" + "┴".join("─" * (w + 2) for _, w in cols) + "┘"


def _table_cells(cols: list[tuple[str, int]], values: list[str]) -> str:
    """Render a row of cells. values[i] is truncated/padded to cols[i][1]."""
    parts = []
    for (_, w), val in zip(cols, values):
        s = str(val)[:w].ljust(w)
        parts.append(f"│ {s} ")
    return "".join(parts) + "│"


def domain_table(rows: list[dict[str, str]], style_header: bool = True) -> str:
    """Render DOMAINS table. Each row: {domain, summary, reqs, planned, qs, assumptions}."""
    cols = DOMAIN_COLS
    lines = [_table_top(cols)]
    labels = [c[0] for c in cols]
    header = _table_cells(cols, labels)
    if style_header:
        header = t(header, BOLD)
    lines.append(header)
    lines.append(_table_sep(cols))
    for r in rows:
        lines.append(
            _table_cells(
                cols,
                [
                    r.get("domain", ""),
                    r.get("summary", ""),
                    r.get("reqs", ""),
                    r.get("planned", ""),
                    r.get("qs", ""),
                    r.get("assumptions", ""),
                ],
            )
        )
    lines.append(_table_bottom(cols))
    return "\n".join(lines)
