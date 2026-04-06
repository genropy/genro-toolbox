"""ASCII and Markdown table rendering utilities."""

import re
import textwrap
from datetime import datetime

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

DEFAULT_MAX_WIDTH = 120
MIN_COLUMN_WIDTH = 6


def strip_ansi(s):
    return ANSI_RE.sub("", s)


def normalize_date_format(fmt: str) -> str:
    mapping = {
        "yyyy": "%Y",
        "yy": "%y",
        "mm": "%m",
        "dd": "%d",
        "HH": "%H",
        "MM": "%M",
        "SS": "%S",
    }
    result = fmt
    for k, v in mapping.items():
        result = result.replace(k, v)
    return result


def parse_bool(value):
    v = str(value).strip().lower()
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0"):
        return False
    return value


def format_cell(value, coldef):
    ctype = coldef.get("type", "str")
    fmt = coldef.get("format")

    if ctype == "str":
        return str(value)
    if ctype == "bool":
        v = parse_bool(value)
        return "true" if v is True else "false" if v is False else str(value)
    if ctype == "int":
        try:
            return str(int(value))
        except Exception:
            return str(value)
    if ctype == "float":
        try:
            f = float(value)
            return format(f, fmt) if fmt else f"{f:g}"
        except Exception:
            return str(value)
    if ctype == "date":
        try:
            d = datetime.fromisoformat(str(value)).date()
        except Exception:
            return str(value)
        return d.strftime(normalize_date_format(fmt)) if fmt else d.isoformat()
    if ctype == "datetime":
        try:
            dt = datetime.fromisoformat(str(value))
        except Exception:
            return str(value)
        return dt.strftime(normalize_date_format(fmt)) if fmt else dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def build_tree(paths, sep):
    tree = {}
    for full in paths:
        parts = str(full).split(sep)
        node = tree
        for p in parts:
            node = node.setdefault(p, {})
    return tree


def flatten_tree(tree, level=0, prefix=""):
    nodes = []
    for key in sorted(tree.keys()):
        full = prefix + key if prefix == "" else prefix + "/" + key
        children = tree[key]
        is_leaf = len(children) == 0
        nodes.append((full, key, level, is_leaf))
        nodes.extend(flatten_tree(children, level + 1, full))
    return nodes


def apply_hierarchy(headers, rows):
    for idx, h in enumerate(headers):
        if "hierarchy" not in h:
            continue
        sep = h["hierarchy"].get("sep", "/")
        original = [r[idx] for r in rows]
        values_by_path = {r[idx]: r[1:] for r in rows}
        tree = build_tree(original, sep)
        tree_items = flatten_tree(tree)
        other_col_count = len(rows[0]) - 1
        expanded_rows = []
        for full, label, level, is_leaf in tree_items:
            values = values_by_path[full] if is_leaf and full in values_by_path else [""] * other_col_count
            expanded_rows.append(["  " * level + label] + values)
        return expanded_rows
    return rows


def compute_col_widths(names, rows, max_width=DEFAULT_MAX_WIDTH, minw=MIN_COLUMN_WIDTH, pad=1):
    usable = max_width - (len(names) + 1)
    widths = []
    min_widths = []  # Minimum width based on longest word

    for i, n in enumerate(names):
        # Find longest word in this column
        longest_word = len(strip_ansi(n))
        for word in strip_ansi(n).split():
            longest_word = max(longest_word, len(word))
        for r in rows:
            cell_str = strip_ansi(str(r[i]))
            for word in cell_str.split():
                longest_word = max(longest_word, len(word))

        # Ideal width (full content) and minimum (longest word)
        ideal = len(strip_ansi(n))
        for r in rows:
            ideal = max(ideal, len(strip_ansi(str(r[i]))))

        widths.append(max(ideal + pad, minw))
        min_widths.append(max(longest_word + pad, minw))

    total = sum(widths)
    if total > usable:
        # First try: ensure no word is broken
        min_total = sum(min_widths)
        if min_total <= usable:
            # Distribute remaining space proportionally
            remaining = usable - min_total
            excess = total - min_total
            for i in range(len(widths)):
                extra = widths[i] - min_widths[i]
                widths[i] = min_widths[i] + int(extra * remaining / excess)
        else:
            # Not enough space even for longest words - scale down proportionally
            scale = usable / sum(min_widths)
            widths = [max(minw, int(w * scale)) for w in min_widths]
    return widths


def wrap_row(row, widths):
    result = []
    for cell, width in zip(row, widths, strict=False):
        s = str(cell)
        has_long_word = any(len(w) > width for w in s.split())
        result.append(
            textwrap.wrap(s, width, break_long_words=has_long_word, break_on_hyphens=False) or [""]
        )
    return result


def merge_wrapped(wrapped):
    max_lines = max(len(col) for col in wrapped)
    return [[col[i] if i < len(col) else "" for col in wrapped] for i in range(max_lines)]


def apply_align(t, w, align):
    if align == "right":
        return t.rjust(w)
    if align == "center":
        return t.center(w)
    return t.ljust(w)


def draw_table(headers, rows, max_width=DEFAULT_MAX_WIDTH):
    names = [h["name"] for h in headers]
    widths = compute_col_widths(names, rows, max_width)

    def sep():
        return "+" + "+".join("-" * w for w in widths) + "+"

    def format_row(row_data):
        lines = []
        for line in merge_wrapped(wrap_row(row_data, widths)):
            lines.append(
                "|"
                + "|".join(
                    apply_align(txt, w, h.get("align", "left"))
                    for txt, w, h in zip(line, widths, headers, strict=False)
                )
                + "|"
            )
        return lines

    out = [sep()]
    out.extend(format_row(names))
    out.append(sep())
    for row in rows:
        out.extend(format_row(row))
        out.append(sep())
    return "\n".join(out)


def render_ascii_table(data, max_width=None):
    headers = data["headers"]
    rows = data["rows"]
    if max_width is None:
        max_width = data.get("max_width", DEFAULT_MAX_WIDTH)
    formatted = [[format_cell(c, h) for c, h in zip(r, headers, strict=False)] for r in rows]
    final = apply_hierarchy(headers, formatted)
    table = draw_table(headers, final, max_width=max_width)
    title = data.get("title")
    return title.center(max_width) + "\n" + table if title else table


def render_markdown_table(data):
    headers = data["headers"]
    rows = data["rows"]
    names = [h["name"] for h in headers]
    out = []
    out.append("| " + " | ".join(names) + " |")
    out.append("| " + " | ".join("---" for _ in names) + " |")
    for r in rows:
        vals = [format_cell(c, h) for c, h in zip(r, headers, strict=False)]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)
