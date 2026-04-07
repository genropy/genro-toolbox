# Copyright 2025 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Boolean expression matcher for tag-based filtering.

Evaluates expressions like ``"admin & !internal"`` against a set of tags.
Supports ``|``/``or``, ``&``/``and``, ``!``/``not``, and parentheses.
"""

from __future__ import annotations

import re

__all__ = ["tags_match", "RuleError"]


class RuleError(ValueError):
    """Raised when a rule expression is invalid."""


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
    if not rule.strip():
        return True

    if len(rule) > max_length:
        raise RuleError(f"Rule too long: {len(rule)} chars (max {max_length})")

    parser = _TagParser(rule, values, max_depth)
    return parser.parse()


class _TagParser:
    """Recursive descent parser for tag expressions."""

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
        self._depth = 0
        self._tokens: list[tuple[str, str]] = []
        self._token_idx = 0
        self._tokenize()

    def _classify_word(self, value: str) -> tuple[str, str]:
        """Classify a WORD token as keyword (AND/OR/NOT) or TAG."""
        _KEYWORDS = {"and": "AND", "or": "OR", "not": "NOT"}
        token_type = _KEYWORDS.get(value.lower(), "TAG")
        return token_type, value

    def _tokenize(self) -> None:
        """Tokenize the input rule."""
        pos = 0
        while pos < len(self._rule):
            match = self._TOKEN_RE.match(self._rule, pos)
            if not match:
                if self._rule[pos:].strip():
                    raise RuleError(
                        f"Invalid character in tag rule at position {pos}: '{self._rule[pos]}'"
                    )
                break

            for name in ("LPAREN", "RPAREN", "NOT", "AND", "OR", "WORD"):
                value = match.group(name)
                if value is not None:
                    if name == "WORD":
                        self._tokens.append(self._classify_word(value))
                    else:
                        self._tokens.append((name, value))
                    break

            pos = match.end()

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
        remaining = self._current()
        if remaining is not None:
            raise RuleError(f"Unexpected token '{remaining[1]}' in: {self._rule}")

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
                raise RuleError(f"Tag rule too deeply nested (max {self._max_depth}): {self._rule}")
            result = self._parse_or()
            self._expect("RPAREN")
            self._depth -= 1
            return result

        if token[0] == "TAG":
            self._advance()
            return token[1] in self._values

        raise RuleError(f"Unexpected token '{token[1]}' in: {self._rule}")
