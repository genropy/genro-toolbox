# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Boolean expression matcher for tag-based filtering.

Evaluates boolean expressions against a set of tags using a recursive
descent parser. No eval() is used - direct evaluation during parsing.

Operators:
    - ``|`` or ``or`` : OR
    - ``&`` or ``and`` : AND
    - ``!`` or ``not`` : NOT (prefix)
    - ``()`` : grouping

Keywords ``and``, ``or``, ``not`` are case-insensitive.

Examples::

    from genro_toolbox import tags_match

    # Simple tag check
    tags_match("admin", {"admin", "user"})  # True
    tags_match("admin", {"user"})  # False

    # OR (pipe or keyword)
    tags_match("admin|public", {"admin"})  # True
    tags_match("admin or public", {"admin"})  # True

    # AND (ampersand or keyword)
    tags_match("admin&internal", {"admin", "internal"})  # True
    tags_match("admin and internal", {"admin", "internal"})  # True
    tags_match("admin&internal", {"admin"})  # False

    # NOT (exclamation or keyword)
    tags_match("!admin", {"public"})  # True
    tags_match("not admin", {"public"})  # True
    tags_match("!admin", {"admin"})  # False

    # Complex expressions
    tags_match("(admin|public)&!internal", {"admin"})  # True
    tags_match("(admin or public) and not internal", {"admin"})  # True
    tags_match("(admin|public)&!internal", {"admin", "internal"})  # False
"""

from __future__ import annotations

import re

__all__ = ["tags_match", "RuleError"]


class RuleError(ValueError):
    """Raised when a rule expression is invalid."""

    pass


def tags_match(
    rule: str,
    values: set[str],
    *,
    max_length: int = 200,
    max_depth: int = 6,
) -> bool:
    """Evaluate a boolean tag expression against a set of values.

    Args:
        rule: Boolean expression string (e.g., "admin&!internal").
        values: Set of tag strings to match against.
        max_length: Maximum allowed length for the rule string.
        max_depth: Maximum nesting depth for parentheses.

    Returns:
        True if the expression matches the given values.

    Raises:
        RuleError: If the rule is invalid or exceeds limits.

    Grammar::

        expr     := or_expr
        or_expr  := and_expr (('|' | 'or') and_expr)*
        and_expr := not_expr (('&' | 'and') not_expr)*
        not_expr := ('!' | 'not') not_expr | primary
        primary  := '(' expr ')' | TAG
        TAG      := [a-zA-Z_][a-zA-Z0-9_]* (excluding keywords)
    """
    if not rule or not rule.strip():
        return True

    if len(rule) > max_length:
        raise RuleError(f"Rule too long: {len(rule)} chars (max {max_length})")

    parser = _TagParser(rule, values, max_depth)
    return parser.parse()


class _TagParser:
    """Recursive descent parser for tag expressions."""

    # Keywords (case-insensitive)
    _KEYWORDS = {"and", "or", "not"}

    # Token patterns
    _TOKEN_RE = re.compile(
        r"""
        \s*                           # skip whitespace
        (?:
            (?P<LPAREN>\()          |
            (?P<RPAREN>\))          |
            (?P<NOT>!)              |
            (?P<AND>&)              |
            (?P<OR>\|)              |
            (?P<WORD>[a-zA-Z_]\w*)
        )
        """,
        re.VERBOSE,
    )

    def __init__(self, rule: str, values: set[str], max_depth: int) -> None:
        self._rule = rule
        self._values = values
        self._max_depth = max_depth
        self._pos = 0
        self._depth = 0
        self._tokens: list[tuple[str, str]] = []
        self._token_idx = 0
        self._tokenize()

    def _tokenize(self) -> None:
        """Tokenize the input rule."""
        pos = 0
        while pos < len(self._rule):
            match = self._TOKEN_RE.match(self._rule, pos)
            if not match:
                # Check if it's just whitespace at end
                if self._rule[pos:].strip():
                    raise RuleError(
                        f"Invalid character in tag rule at position {pos}: "
                        f"'{self._rule[pos]}'"
                    )
                break

            # Find which group matched
            for name in ("LPAREN", "RPAREN", "NOT", "AND", "OR", "WORD"):
                value = match.group(name)
                if value is not None:
                    # Convert keywords to their token types
                    if name == "WORD":
                        lower = value.lower()
                        if lower == "and":
                            self._tokens.append(("AND", value))
                        elif lower == "or":
                            self._tokens.append(("OR", value))
                        elif lower == "not":
                            self._tokens.append(("NOT", value))
                        else:
                            self._tokens.append(("TAG", value))
                    else:
                        self._tokens.append((name, value))
                    break

            pos = match.end()

        # Check for remaining non-whitespace
        remaining = self._rule[pos:].strip()
        if remaining:
            raise RuleError(f"Invalid character in tag rule: '{remaining[0]}'")

    def _current(self) -> tuple[str, str] | None:
        """Get current token or None if exhausted."""
        if self._token_idx < len(self._tokens):
            return self._tokens[self._token_idx]
        return None

    def _advance(self) -> tuple[str, str] | None:
        """Consume current token and return it."""
        token = self._current()
        if token:
            self._token_idx += 1
        return token

    def _expect(self, token_type: str) -> str:
        """Consume token of expected type or raise error."""
        token = self._current()
        if not token or token[0] != token_type:
            expected = token_type
            got = token[0] if token else "end of expression"
            raise RuleError(f"Expected {expected}, got {got} in: {self._rule}")
        self._advance()
        return token[1]

    def parse(self) -> bool:
        """Parse and evaluate the expression."""
        if not self._tokens:
            return True

        result = self._parse_or()

        # Ensure all tokens consumed
        if self._current() is not None:
            token = self._current()
            raise RuleError(
                f"Unexpected token '{token[1]}' in: {self._rule}"  # type: ignore[index]
            )

        return result

    def _parse_or(self) -> bool:
        """Parse OR expression: and_expr ('|' and_expr)*"""
        left = self._parse_and()

        while True:
            token = self._current()
            if token and token[0] == "OR":
                self._advance()
                right = self._parse_and()
                left = left or right
            else:
                break

        return left

    def _parse_and(self) -> bool:
        """Parse AND expression: not_expr ('&' not_expr)*"""
        left = self._parse_not()

        while True:
            token = self._current()
            if token and token[0] == "AND":
                self._advance()
                right = self._parse_not()
                left = left and right
            else:
                break

        return left

    def _parse_not(self) -> bool:
        """Parse NOT expression: '!' not_expr | primary"""
        token = self._current()
        if token and token[0] == "NOT":
            self._advance()
            return not self._parse_not()
        return self._parse_primary()

    def _parse_primary(self) -> bool:
        """Parse primary: '(' expr ')' | TAG"""
        token = self._current()

        if not token:
            raise RuleError(f"Unexpected end of expression: {self._rule}")

        if token[0] == "LPAREN":
            self._advance()
            self._depth += 1
            if self._depth > self._max_depth:
                raise RuleError(
                    f"Tag rule too deeply nested (max {self._max_depth}): {self._rule}"
                )
            result = self._parse_or()
            self._expect("RPAREN")
            self._depth -= 1
            return result

        if token[0] == "TAG":
            self._advance()
            return token[1] in self._values

        raise RuleError(f"Unexpected token '{token[1]}' in: {self._rule}")
