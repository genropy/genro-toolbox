# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Tests for tags_match module."""

from __future__ import annotations

import pytest

from genro_toolbox.tags_match import RuleError, tags_match


class TestBasicMatching:
    """Test basic tag matching."""

    def test_single_tag_match(self):
        assert tags_match("admin", {"admin", "internal"}) is True

    def test_single_tag_no_match(self):
        assert tags_match("admin", {"public"}) is False

    def test_empty_rule_returns_true(self):
        assert tags_match("", {"admin"}) is True
        assert tags_match("   ", {"admin"}) is True

    def test_empty_values_no_match(self):
        assert tags_match("admin", set()) is False

    def test_empty_values_with_not(self):
        assert tags_match("!admin", set()) is True


class TestOrOperator:
    """Test OR operator (pipe)."""

    def test_or_with_pipe(self):
        assert tags_match("admin|public", {"admin"}) is True
        assert tags_match("admin|public", {"public"}) is True
        assert tags_match("admin|public", {"internal"}) is False

    def test_multiple_or(self):
        assert tags_match("a|b|c", {"a"}) is True
        assert tags_match("a|b|c", {"c"}) is True
        assert tags_match("a|b|c", {"d"}) is False

    def test_comma_not_allowed(self):
        """Comma is not allowed in rules - raises error."""
        with pytest.raises(RuleError, match="Invalid character"):
            tags_match("admin,public", {"admin"})


class TestAndOperator:
    """Test AND operator."""

    def test_and_both_present(self):
        assert tags_match("admin&internal", {"admin", "internal"}) is True

    def test_and_missing_one(self):
        assert tags_match("admin&internal", {"admin"}) is False
        assert tags_match("admin&internal", {"internal"}) is False

    def test_multiple_and(self):
        assert tags_match("a&b&c", {"a", "b", "c"}) is True
        assert tags_match("a&b&c", {"a", "b"}) is False


class TestNotOperator:
    """Test NOT operator."""

    def test_not_absent(self):
        assert tags_match("!admin", {"public"}) is True

    def test_not_present(self):
        assert tags_match("!admin", {"admin"}) is False

    def test_double_not(self):
        assert tags_match("!!admin", {"admin"}) is True
        assert tags_match("!!admin", {"public"}) is False

    def test_not_with_and(self):
        assert tags_match("public&!internal", {"public"}) is True
        assert tags_match("public&!internal", {"public", "internal"}) is False

    def test_not_with_or(self):
        # NOT admin OR NOT internal (true unless both present)
        assert tags_match("!admin|!internal", {"public"}) is True
        assert tags_match("!admin|!internal", {"admin"}) is True
        assert tags_match("!admin|!internal", {"internal"}) is True
        assert tags_match("!admin|!internal", {"admin", "internal"}) is False


class TestParentheses:
    """Test parentheses grouping."""

    def test_simple_grouping(self):
        expr = "(admin|public)&internal"
        assert tags_match(expr, {"admin", "internal"}) is True
        assert tags_match(expr, {"public", "internal"}) is True
        assert tags_match(expr, {"admin"}) is False
        assert tags_match(expr, {"internal"}) is False

    def test_grouping_with_not(self):
        expr = "(admin|public)&!internal"
        assert tags_match(expr, {"admin"}) is True
        assert tags_match(expr, {"public"}) is True
        assert tags_match(expr, {"admin", "internal"}) is False
        assert tags_match(expr, {"other"}) is False

    def test_nested_parentheses(self):
        expr = "((admin|public)&internal)|superuser"
        assert tags_match(expr, {"admin", "internal"}) is True
        assert tags_match(expr, {"public", "internal"}) is True
        assert tags_match(expr, {"superuser"}) is True
        assert tags_match(expr, {"admin"}) is False
        assert tags_match(expr, {"internal"}) is False

    def test_not_outside_parentheses(self):
        expr = "!(admin&internal)"
        assert tags_match(expr, {"admin"}) is True
        assert tags_match(expr, {"internal"}) is True
        assert tags_match(expr, {"admin", "internal"}) is False
        assert tags_match(expr, {"public"}) is True


class TestComplexExpressions:
    """Test complex boolean expressions."""

    def test_multiple_not_with_and(self):
        expr = "!admin&!internal"
        assert tags_match(expr, {"public"}) is True
        assert tags_match(expr, {"admin"}) is False
        assert tags_match(expr, {"internal"}) is False
        assert tags_match(expr, {"admin", "internal"}) is False
        assert tags_match(expr, set()) is True

    def test_three_tags_complex(self):
        expr = "(admin&internal)|(public&external)"
        assert tags_match(expr, {"admin", "internal"}) is True
        assert tags_match(expr, {"public", "external"}) is True
        assert tags_match(expr, {"admin", "external"}) is False
        assert tags_match(expr, {"admin"}) is False

    def test_mixed_operators(self):
        expr = "a&b|c&d"  # (a AND b) OR (c AND d)
        assert tags_match(expr, {"a", "b"}) is True
        assert tags_match(expr, {"c", "d"}) is True
        assert tags_match(expr, {"a", "c"}) is False
        assert tags_match(expr, {"a", "d"}) is False


class TestWhitespace:
    """Test whitespace handling."""

    def test_whitespace_around_operators(self):
        assert tags_match(" admin & internal ", {"admin", "internal"}) is True
        assert tags_match("admin | public", {"admin"}) is True
        assert tags_match("! admin", {"public"}) is True

    def test_whitespace_around_parentheses(self):
        assert tags_match("( admin | public )", {"admin"}) is True


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_character(self):
        with pytest.raises(RuleError, match="Invalid character"):
            tags_match("admin; drop table", {"admin"})

    def test_unmatched_parenthesis_open(self):
        with pytest.raises(RuleError):
            tags_match("(admin", {"admin"})

    def test_unmatched_parenthesis_close(self):
        with pytest.raises(RuleError):
            tags_match("admin)", {"admin"})

    def test_empty_parentheses(self):
        with pytest.raises(RuleError):
            tags_match("()", {"admin"})

    def test_double_operator(self):
        with pytest.raises(RuleError):
            tags_match("admin&&public", {"admin"})

    def test_operator_at_start(self):
        with pytest.raises(RuleError):
            tags_match("&admin", {"admin"})

    def test_operator_at_end(self):
        with pytest.raises(RuleError):
            tags_match("admin&", {"admin"})


class TestLimits:
    """Test safety limits."""

    def test_max_length_exceeded(self):
        long_rule = "a" * 201
        with pytest.raises(RuleError, match="too long"):
            tags_match(long_rule, {"a"})

    def test_max_length_custom(self):
        with pytest.raises(RuleError, match="too long"):
            tags_match("admin", {"admin"}, max_length=3)

    def test_max_depth_exceeded(self):
        # 7 levels of nesting
        deep_rule = "(((((((" + "a" + ")))))))"
        with pytest.raises(RuleError, match="deeply nested"):
            tags_match(deep_rule, {"a"})

    def test_max_depth_custom(self):
        rule = "((a))"  # 2 levels
        with pytest.raises(RuleError, match="deeply nested"):
            tags_match(rule, {"a"}, max_depth=1)

    def test_max_depth_ok(self):
        rule = "((((((a))))))"  # 6 levels - should be ok
        assert tags_match(rule, {"a"}) is True


class TestTagNames:
    """Test valid tag name patterns."""

    def test_underscore_prefix(self):
        assert tags_match("_private", {"_private"}) is True

    def test_underscore_in_name(self):
        assert tags_match("admin_user", {"admin_user"}) is True

    def test_numbers_in_name(self):
        assert tags_match("level2", {"level2"}) is True

    def test_uppercase(self):
        assert tags_match("ADMIN", {"ADMIN"}) is True
        assert tags_match("Admin", {"Admin"}) is True

    def test_mixed_case(self):
        assert tags_match("AdminUser", {"AdminUser"}) is True


class TestKeywordOperators:
    """Test and/or/not keyword operators."""

    def test_or_keyword(self):
        assert tags_match("admin or public", {"admin"}) is True
        assert tags_match("admin or public", {"public"}) is True
        assert tags_match("admin or public", {"internal"}) is False

    def test_or_keyword_case_insensitive(self):
        assert tags_match("admin OR public", {"admin"}) is True
        assert tags_match("admin Or public", {"public"}) is True

    def test_and_keyword(self):
        assert tags_match("admin and internal", {"admin", "internal"}) is True
        assert tags_match("admin and internal", {"admin"}) is False

    def test_and_keyword_case_insensitive(self):
        assert tags_match("admin AND internal", {"admin", "internal"}) is True
        assert tags_match("admin And internal", {"admin", "internal"}) is True

    def test_not_keyword(self):
        assert tags_match("not admin", {"public"}) is True
        assert tags_match("not admin", {"admin"}) is False

    def test_not_keyword_case_insensitive(self):
        assert tags_match("NOT admin", {"public"}) is True
        assert tags_match("Not admin", {"public"}) is True

    def test_complex_with_keywords(self):
        expr = "(admin or public) and not internal"
        assert tags_match(expr, {"admin"}) is True
        assert tags_match(expr, {"public"}) is True
        assert tags_match(expr, {"admin", "internal"}) is False

    def test_mixed_symbols_and_keywords(self):
        # Mix & with 'or', | with 'and', etc.
        assert tags_match("admin & public or internal", {"internal"}) is True
        assert tags_match("admin | public and internal", {"admin"}) is True
        assert tags_match("!admin and not internal", {"public"}) is True

    def test_keyword_not_as_tag_name(self):
        # Keywords should not be usable as tag names
        # "and" is interpreted as operator, not tag
        # So "and" alone should fail (operator without operands)
        with pytest.raises(RuleError):
            tags_match("and", {"and"})

    def test_tag_starting_with_keyword(self):
        # Tags that START with keyword letters but are different
        assert tags_match("android", {"android"}) is True
        assert tags_match("notice", {"notice"}) is True
        assert tags_match("order", {"order"}) is True
