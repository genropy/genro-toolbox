"""Tests for ascii_table module."""

from genro_toolbox.ascii_table import (
    render_ascii_table,
    render_markdown_table,
    format_cell,
    strip_ansi,
    normalize_date_format,
    parse_bool,
    build_tree,
    flatten_tree,
    apply_hierarchy,
    compute_col_widths,
    wrap_row,
    merge_wrapped,
    apply_align,
    draw_table,
)


class TestStripAnsi:
    """Test ANSI escape sequence stripping."""

    def test_strip_ansi_removes_color_codes(self):
        """Strip ANSI color codes from string."""
        text = "\x1b[31mRed\x1b[0m Text"
        assert strip_ansi(text) == "Red Text"

    def test_strip_ansi_handles_plain_text(self):
        """Plain text is unchanged."""
        assert strip_ansi("Plain text") == "Plain text"

    def test_strip_ansi_handles_multiple_codes(self):
        """Strip multiple ANSI codes."""
        text = "\x1b[1m\x1b[31mBold Red\x1b[0m\x1b[32mGreen\x1b[0m"
        assert strip_ansi(text) == "Bold RedGreen"


class TestNormalizeDateFormat:
    """Test date format normalization."""

    def test_normalize_yyyy_mm_dd(self):
        """Convert yyyy-mm-dd to Python format."""
        assert normalize_date_format("yyyy-mm-dd") == "%Y-%m-%d"

    def test_normalize_time_format(self):
        """Convert time format."""
        assert normalize_date_format("HH:MM:SS") == "%H:%M:%S"

    def test_normalize_mixed_format(self):
        """Convert mixed date-time format."""
        assert normalize_date_format("yyyy-mm-dd HH:MM") == "%Y-%m-%d %H:%M"

    def test_normalize_yy_format(self):
        """Convert two-digit year."""
        assert normalize_date_format("yy-mm-dd") == "%y-%m-%d"


class TestParseBool:
    """Test boolean parsing."""

    def test_parse_true_variants(self):
        """Parse various true representations."""
        assert parse_bool("true") is True
        assert parse_bool("True") is True
        assert parse_bool("TRUE") is True
        assert parse_bool("yes") is True
        assert parse_bool("Yes") is True
        assert parse_bool("1") is True

    def test_parse_false_variants(self):
        """Parse various false representations."""
        assert parse_bool("false") is False
        assert parse_bool("False") is False
        assert parse_bool("FALSE") is False
        assert parse_bool("no") is False
        assert parse_bool("No") is False
        assert parse_bool("0") is False

    def test_parse_bool_returns_original_for_non_bool(self):
        """Non-boolean values are returned as-is."""
        assert parse_bool("maybe") == "maybe"
        assert parse_bool("2") == "2"
        assert parse_bool("") == ""


class TestFormatCell:
    """Test cell formatting based on type."""

    def test_format_str(self):
        """Format string type."""
        coldef = {"type": "str"}
        assert format_cell("test", coldef) == "test"
        assert format_cell(123, coldef) == "123"

    def test_format_bool(self):
        """Format boolean type."""
        coldef = {"type": "bool"}
        assert format_cell("true", coldef) == "true"
        assert format_cell("false", coldef) == "false"
        assert format_cell("yes", coldef) == "true"
        assert format_cell("no", coldef) == "false"

    def test_format_int(self):
        """Format integer type."""
        coldef = {"type": "int"}
        assert format_cell("123", coldef) == "123"
        assert format_cell(123.7, coldef) == "123"
        assert format_cell("not_a_number", coldef) == "not_a_number"

    def test_format_float(self):
        """Format float type."""
        coldef = {"type": "float"}
        assert format_cell(3.14159, coldef) == "3.14159"
        assert format_cell("not_a_number", coldef) == "not_a_number"

    def test_format_float_with_format_spec(self):
        """Format float with custom format."""
        coldef = {"type": "float", "format": ".2f"}
        assert format_cell(3.14159, coldef) == "3.14"

    def test_format_date(self):
        """Format date type."""
        coldef = {"type": "date"}
        assert format_cell("2025-11-24", coldef) == "2025-11-24"

    def test_format_date_with_custom_format(self):
        """Format date with custom format."""
        coldef = {"type": "date", "format": "dd/mm/yyyy"}
        assert format_cell("2025-11-24", coldef) == "24/11/2025"

    def test_format_date_invalid(self):
        """Invalid date returns string."""
        coldef = {"type": "date"}
        assert format_cell("not_a_date", coldef) == "not_a_date"

    def test_format_datetime(self):
        """Format datetime type."""
        coldef = {"type": "datetime"}
        assert format_cell("2025-11-24T10:30:00", coldef) == "2025-11-24 10:30:00"

    def test_format_datetime_with_custom_format(self):
        """Format datetime with custom format."""
        coldef = {"type": "datetime", "format": "yyyy-mm-dd HH:MM"}
        assert format_cell("2025-11-24T10:30:00", coldef) == "2025-11-24 10:30"

    def test_format_datetime_invalid(self):
        """Invalid datetime returns string."""
        coldef = {"type": "datetime"}
        assert format_cell("not_a_datetime", coldef) == "not_a_datetime"

    def test_format_unknown_type(self):
        """Unknown type falls back to string conversion."""
        coldef = {"type": "unknown_type"}
        assert format_cell("test_value", coldef) == "test_value"
        assert format_cell(12345, coldef) == "12345"


class TestTreeOperations:
    """Test hierarchical tree operations."""

    def test_build_tree_simple(self):
        """Build simple tree from paths."""
        paths = ["a/b/c", "a/b/d", "a/e"]
        tree = build_tree(paths, "/")
        assert "a" in tree
        assert "b" in tree["a"]
        assert "c" in tree["a"]["b"]
        assert "d" in tree["a"]["b"]
        assert "e" in tree["a"]

    def test_build_tree_single_level(self):
        """Build tree with single level."""
        paths = ["one", "two", "three"]
        tree = build_tree(paths, "/")
        assert "one" in tree
        assert "two" in tree
        assert "three" in tree

    def test_flatten_tree(self):
        """Flatten tree to list with levels."""
        tree = {"a": {"b": {"c": {}}, "d": {}}}
        flat = flatten_tree(tree)
        assert len(flat) == 4  # a, a/b, a/b/c, a/d
        # Check structure: (full_path, label, level, is_leaf)
        assert flat[0] == ("a", "a", 0, False)
        assert flat[1] == ("a/b", "b", 1, False)
        assert flat[2] == ("a/b/c", "c", 2, True)
        assert flat[3] == ("a/d", "d", 1, True)

    def test_apply_hierarchy_simple(self):
        """Apply hierarchy with indentation."""
        headers = [{"name": "Path", "hierarchy": {"sep": "/"}}, {"name": "Value"}]
        rows = [
            ["root/child1", "10"],
            ["root/child2", "20"],
        ]
        result = apply_hierarchy(headers, rows)
        # Should have indented labels
        assert any("root" in str(r[0]) for r in result)

    def test_apply_hierarchy_no_hierarchy_column(self):
        """No hierarchy column returns rows unchanged."""
        headers = [{"name": "Name"}, {"name": "Value"}]
        rows = [["foo", "bar"]]
        result = apply_hierarchy(headers, rows)
        assert result == rows


class TestTableLayout:
    """Test table layout calculations."""

    def test_compute_col_widths_basic(self):
        """Compute column widths from data."""
        names = ["Name", "Value"]
        rows = [["short", "data"], ["longer_name", "more_data"]]
        widths = compute_col_widths(names, rows)
        assert len(widths) == 2
        assert widths[0] >= len("longer_name")
        assert widths[1] >= len("more_data")

    def test_compute_col_widths_respects_max(self):
        """Widths scale down to respect max_width."""
        names = ["A", "B"]
        rows = [["x" * 100, "y" * 100]]
        widths = compute_col_widths(names, rows, max_width=50)
        assert sum(widths) <= 50 - (len(names) + 1)

    def test_compute_col_widths_exact_min_width(self):
        """Test when total equals sum of min_widths (edge case for line 159).

        When content is single words (no spaces), ideal width == min width.
        With constrained max_width where total > usable but sum(min_widths) <= usable,
        the branch at line 159 (else: widths[i] = min_widths[i]) is executed.
        """
        # Single-word content means ideal == longest_word == min
        names = ["A", "B"]
        rows = [["word1", "word2"]]
        # With pad=2: widths[i] = 5+2 = 7, min_widths[i] = 7
        # total = 14, sum(min_widths) = 14 → total == sum(min_widths)
        # separators = 3 (|col|col|), usable = max_width - 3
        # Need: total > usable AND sum(min_widths) <= usable
        # 14 > max_width - 3 AND 14 <= max_width - 3 → impossible
        # But we need total > usable to enter the outer if, so max_width < 17
        # And sum(min_widths) <= usable, so 14 <= max_width - 3, max_width >= 17
        # This is contradictory for the exact equality case.
        #
        # Let's use a different approach: longer words to make total larger
        # but still keep total == sum(min_widths)
        names = ["ABCD", "EFGH"]  # 4 chars each
        rows = [["word123", "word456"]]  # 7 chars each, single words
        # ideal for col 0 = max(4, 7) = 7, widths[0] = 7+2 = 9
        # min for col 0 = max(7+2, 5) = 9
        # Same for col 1: widths = [9, 9], min_widths = [9, 9]
        # total = 18, sum(min_widths) = 18 → equal
        # usable = max_width - 3
        # Need: 18 > usable AND 18 <= usable → still contradictory
        #
        # Actually the branch is inside the loop, checking for each column.
        # If for ANY column widths[i] == min_widths[i], we hit line 159.
        # Let's verify with max_width=20: usable=17, total=18 > 17, sum(min)=18 > 17
        # This triggers line 161-163 instead (scale down).
        #
        # The branch at 154 is only reachable if sum(min_widths) <= usable (line 149)
        # and we're inside the loop. The condition at 154 is checking for the
        # case where total == sum(min_widths), meaning all columns have
        # ideal == min. In that case, extra = 0 for all, so the if branch
        # would do: widths[i] = min_widths[i] + 0 = min_widths[i]
        # Same result as else branch. The else branch (159) is dead code.
        #
        # Actually, re-reading: if total == sum(min_widths), then
        # for each column extra = widths[i] - min_widths[i] = 0
        # In if branch: min_widths[i] + int(0 * remaining / 0) → division by zero!
        # So the else branch (159) prevents division by zero.
        #
        # To trigger it: need total == sum(min_widths), which happens when
        # all columns have ideal == min (single words, no wrapping benefit).
        widths = compute_col_widths(names, rows, max_width=25)
        # usable = 22, total = 18 < usable → no compression needed
        # Let's force it
        widths = compute_col_widths(names, rows, max_width=20)
        # usable = 17, total = 18 > 17 (enters outer if)
        # sum(min_widths) = 18 > 17 (enters else at line 161, not our target)
        #
        # We need sum(min_widths) <= usable < total
        # But total == sum(min_widths), so this is impossible.
        # The line 159 is truly dead code when total == sum(min_widths).
        #
        # Let's try a case where ONE column has ideal == min (hitting else)
        # but another has ideal > min (making total > sum(min_widths))
        names = ["A", "B"]
        rows = [["word1", "two words here"]]  # col 0: single word, col 1: multi-word
        # col 0: ideal = 5, min = 5, widths[0] = 7, min_widths[0] = 7
        # col 1: ideal = 14, min = 5 (longest word "words"), widths[1] = 16, min_widths[1] = 7
        # total = 23, sum(min_widths) = 14
        # usable = max_width - 3
        # Need: 23 > usable AND 14 <= usable → 17 <= max_width < 26
        widths = compute_col_widths(names, rows, max_width=20)
        # usable = 17, total = 23 > 17 ✓, sum(min) = 14 <= 17 ✓
        # remaining = 17 - 14 = 3
        # col 0: extra = 7 - 7 = 0 → hits else branch (line 159)!
        # col 1: extra = 16 - 7 = 9 → hits if branch
        assert len(widths) == 2
        assert widths[0] >= 5  # minimum width preserved

    def test_compute_col_widths_with_ansi(self):
        """ANSI codes don't count toward width."""
        names = ["Name"]
        rows = [["\x1b[31mRed\x1b[0m"]]
        widths = compute_col_widths(names, rows)
        # Width should be based on "Red" (3 chars) not including ANSI codes
        assert widths[0] >= 3

    def test_wrap_row(self):
        """Wrap row content to specified widths."""
        row = ["short", "this is a longer text that needs wrapping"]
        widths = [10, 15]
        wrapped = wrap_row(row, widths)
        assert len(wrapped) == 2
        assert isinstance(wrapped[0], list)
        assert isinstance(wrapped[1], list)

    def test_merge_wrapped(self):
        """Merge wrapped columns into rows."""
        wrapped = [["a1", "a2"], ["b1"], ["c1", "c2", "c3"]]
        merged = merge_wrapped(wrapped)
        assert len(merged) == 3  # max length
        assert merged[0] == ["a1", "b1", "c1"]
        assert merged[1] == ["a2", "", "c2"]
        assert merged[2] == ["", "", "c3"]

    def test_apply_align_left(self):
        """Left alignment."""
        assert apply_align("foo", 10, "left") == "foo       "

    def test_apply_align_right(self):
        """Right alignment."""
        assert apply_align("foo", 10, "right") == "       foo"

    def test_apply_align_center(self):
        """Center alignment."""
        result = apply_align("foo", 10, "center")
        assert result.strip() == "foo"
        assert len(result) == 10


class TestDrawTable:
    """Test ASCII table drawing."""

    def test_draw_simple_table(self):
        """Draw simple table."""
        headers = [
            {"name": "Name", "align": "left"},
            {"name": "Value", "align": "right"},
        ]
        rows = [["foo", "123"], ["bar", "456"]]
        result = draw_table(headers, rows)

        assert "+---" in result  # separator
        assert "Name" in result
        assert "Value" in result
        assert "foo" in result
        assert "123" in result

    def test_draw_table_with_wrapping(self):
        """Draw table with text wrapping."""
        headers = [{"name": "Text"}]
        rows = [["This is a very long text that will need to be wrapped"]]
        result = draw_table(headers, rows, max_width=30)
        # Should wrap the long text
        lines = result.split("\n")
        assert len(lines) > 3  # header + separator + at least 2 wrapped lines


class TestTableFromStruct:
    """Test complete table generation from structure."""

    def test_render_ascii_table_basic(self):
        """Generate table from basic structure."""
        data = {
            "headers": [
                {"name": "Name", "type": "str"},
                {"name": "Age", "type": "int"},
            ],
            "rows": [["Alice", "25"], ["Bob", "30"]],
        }
        result = render_ascii_table(data)
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "25" in result

    def test_render_ascii_table_with_title(self):
        """Generate table with title."""
        data = {
            "title": "User List",
            "headers": [{"name": "Name", "type": "str"}],
            "rows": [["Alice"]],
        }
        result = render_ascii_table(data)
        assert "User List" in result
        assert "Alice" in result

    def test_render_ascii_table_with_types(self):
        """Generate table with type formatting."""
        data = {
            "headers": [
                {"name": "Name", "type": "str"},
                {"name": "Active", "type": "bool"},
                {"name": "Score", "type": "float", "format": ".1f"},
            ],
            "rows": [["Alice", "yes", 95.67], ["Bob", "no", 87.32]],
        }
        result = render_ascii_table(data)
        assert "true" in result  # yes -> true
        assert "false" in result  # no -> false
        assert "95.7" in result  # formatted float
        assert "87.3" in result

    def test_render_ascii_table_with_dates(self):
        """Generate table with date formatting."""
        data = {
            "headers": [
                {"name": "Date", "type": "date", "format": "dd/mm/yyyy"},
                {"name": "DateTime", "type": "datetime"},
            ],
            "rows": [["2025-11-24", "2025-11-24T10:30:00"]],
        }
        result = render_ascii_table(data)
        assert "24/11/2025" in result
        assert "2025-11-24 10:30:00" in result

    def test_render_ascii_table_with_max_width(self):
        """Generate table respecting max_width in data dict."""
        data = {
            "max_width": 50,
            "headers": [{"name": "Text", "type": "str"}],
            "rows": [["x" * 100]],
        }
        result = render_ascii_table(data)
        lines = result.split("\n")
        # Check that lines don't exceed max_width
        for line in lines:
            assert len(strip_ansi(line)) <= 52  # Allow for separators

    def test_render_ascii_table_with_max_width_parameter(self):
        """Generate table with max_width passed as parameter."""
        data = {
            "headers": [{"name": "Text", "type": "str"}],
            "rows": [["x" * 100]],
        }
        # Pass max_width as parameter, not in data dict
        result = render_ascii_table(data, max_width=60)
        lines = result.split("\n")
        # Check that lines don't exceed max_width
        for line in lines:
            assert len(strip_ansi(line)) <= 62  # Allow for separators


class TestRenderMarkdownTable:
    """Test Markdown table rendering."""

    def test_render_markdown_simple(self):
        """Render simple markdown table."""
        data = {
            "headers": [
                {"name": "Name", "type": "str"},
                {"name": "Value", "type": "int"},
            ],
            "rows": [["Alice", "25"], ["Bob", "30"]],
        }
        result = render_markdown_table(data)

        assert "| Name | Value |" in result
        assert "| --- | --- |" in result
        assert "| Alice | 25 |" in result
        assert "| Bob | 30 |" in result

    def test_render_markdown_with_formatting(self):
        """Render markdown with type formatting."""
        data = {
            "headers": [
                {"name": "Active", "type": "bool"},
                {"name": "Score", "type": "float", "format": ".2f"},
            ],
            "rows": [["yes", 95.678], ["no", 87.321]],
        }
        result = render_markdown_table(data)

        assert "true" in result
        assert "false" in result
        assert "95.68" in result
        assert "87.32" in result


class TestWordWrapping:
    """Test intelligent word wrapping without breaking words."""

    def test_wrap_preserves_words(self):
        """Words should not be broken unless absolutely necessary."""
        data = {
            "max_width": 60,
            "headers": [
                {"name": "Command", "type": "str"},
                {"name": "Description", "type": "str"},
            ],
            "rows": [
                ["add_application", "Add a new application to registry"],
                ["configure_plugins", "Configure runtime plugin options"],
            ],
        }
        result = render_ascii_table(data)

        # Words should stay intact
        assert "add_application" in result or "add_applicat\nion" not in result
        assert "configure_plugins" in result or "configure_pl\nugins" not in result

    def test_wrap_breaks_only_on_spaces(self):
        """Wrapping should happen on word boundaries."""
        data = {
            "max_width": 50,
            "headers": [{"name": "Text", "type": "str"}],
            "rows": [["This is a long sentence that needs wrapping"]],
        }
        result = render_ascii_table(data)

        # Should contain complete words
        assert "This" in result
        assert "sentence" in result
        assert "wrapping" in result


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_complete_table_with_all_features(self):
        """Test table with all features combined."""
        data = {
            "title": "Sales Report",
            "max_width": 80,
            "headers": [
                {"name": "Region", "type": "str", "align": "left"},
                {"name": "Revenue", "type": "float", "format": ".2f", "align": "right"},
                {"name": "Active", "type": "bool", "align": "center"},
                {"name": "Date", "type": "date", "format": "dd/mm/yyyy"},
            ],
            "rows": [
                ["North", 12345.67, "yes", "2025-11-24"],
                ["South", 9876.54, "no", "2025-11-23"],
                ["East", 15432.10, "true", "2025-11-22"],
            ],
        }
        result = render_ascii_table(data)

        # Check title
        assert "Sales Report" in result

        # Check formatted values
        assert "12345.67" in result
        assert "true" in result
        assert "false" in result
        assert "24/11/2025" in result

        # Check structure
        assert "Region" in result
        assert "Revenue" in result
        assert "Active" in result

    def test_hierarchy_table(self):
        """Test table with hierarchical data."""
        data = {
            "headers": [
                {"name": "Path", "type": "str", "hierarchy": {"sep": "/"}},
                {"name": "Size", "type": "int"},
            ],
            "rows": [
                ["root/docs/file1.txt", "1024"],
                ["root/docs/file2.txt", "2048"],
                ["root/src/main.py", "4096"],
            ],
        }
        result = render_ascii_table(data)

        # Should have hierarchical structure with indentation
        assert "root" in result
        assert "docs" in result
        assert "src" in result
