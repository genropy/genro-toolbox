# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""TreeStore - A hierarchical structure with builder pattern support.

This module provides:
- TreeStoreNode: A node with label, attributes, and value (scalar or TreeStore)
- TreeStore: A container of TreeStoreNodes with parent reference
- TreeStoreBuilder: Base builder class for fluent tree construction
- valid_children: Decorator for child validation in typed builders
"""

from __future__ import annotations

from typing import Any, Callable, Iterator


class TreeStoreNode:
    """A node in a TreeStore hierarchy.

    Each node has:
    - label: The node's name/key
    - attr: Dictionary of attributes
    - value: Either a scalar value or a TreeStore (for children)
    - parent: Reference to the containing TreeStore

    Example:
        >>> node = TreeStoreNode('user', {'id': 1}, 'Alice')
        >>> node.label
        'user'
        >>> node.attr
        {'id': 1}
        >>> node.value
        'Alice'
    """

    __slots__ = ('label', 'attr', 'value', 'parent')

    def __init__(
        self,
        label: str,
        attr: dict[str, Any] | None = None,
        value: Any | TreeStore = None,
        parent: TreeStore | None = None,
    ) -> None:
        """Initialize a TreeStoreNode.

        Args:
            label: The node's name/key.
            attr: Optional dictionary of attributes.
            value: The node's value (scalar or TreeStore for children).
            parent: The TreeStore containing this node.
        """
        self.label = label
        self.attr = attr or {}
        self.value = value
        self.parent = parent

    def __repr__(self) -> str:
        value_repr = (
            f"TreeStore({len(self.value)})"
            if isinstance(self.value, TreeStore)
            else repr(self.value)
        )
        return f"TreeStoreNode({self.label!r}, attr={self.attr}, value={value_repr})"

    @property
    def is_branch(self) -> bool:
        """True if this node contains a TreeStore (has children)."""
        return isinstance(self.value, TreeStore)

    @property
    def is_leaf(self) -> bool:
        """True if this node contains a scalar value."""
        return not isinstance(self.value, TreeStore)

    @property
    def root(self) -> TreeStore:
        """Get the root TreeStore of this node's hierarchy."""
        if self.parent is None:
            raise ValueError("Node has no parent")
        return self.parent.root


class TreeStore:
    """A container of TreeStoreNodes with hierarchical navigation.

    TreeStore maintains:
    - nodes: Dictionary of {label: TreeStoreNode}
    - parent: Reference to the TreeStoreNode that contains this store

    The dual relationship enables bidirectional traversal:
    - node.parent -> TreeStore containing the node
    - store.parent -> TreeStoreNode that has this store as value

    Example:
        >>> store = TreeStore()
        >>> store.add_node('name', value='Alice')
        >>> store['name'].value
        'Alice'
    """

    __slots__ = ('nodes', 'parent', '_tag')

    def __init__(self, parent: TreeStoreNode | None = None) -> None:
        """Initialize a TreeStore.

        Args:
            parent: The TreeStoreNode that contains this store as its value.
        """
        self.nodes: dict[str, TreeStoreNode] = {}
        self.parent = parent
        self._tag: str | None = None  # Tag for validation context

    def __repr__(self) -> str:
        return f"TreeStore({list(self.nodes.keys())})"

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self) -> Iterator[str]:
        return iter(self.nodes)

    def __contains__(self, label: str) -> bool:
        return label in self.nodes

    def __getitem__(self, label: str) -> TreeStoreNode:
        return self.nodes[label]

    def add_node(
        self,
        label: str,
        attr: dict[str, Any] | None = None,
        value: Any | TreeStore = None,
    ) -> TreeStoreNode:
        """Add a node to this store.

        Args:
            label: The node's name/key.
            attr: Optional dictionary of attributes.
            value: The node's value.

        Returns:
            The created TreeStoreNode.
        """
        node = TreeStoreNode(label, attr, value, parent=self)
        self.nodes[label] = node
        return node

    def add_branch(
        self, label: str, attr: dict[str, Any] | None = None
    ) -> TreeStoreNode:
        """Add a branch node (with TreeStore as value).

        Args:
            label: The node's name/key.
            attr: Optional dictionary of attributes.

        Returns:
            The created TreeStoreNode with a TreeStore as value.
        """
        child_store = TreeStore()
        node = TreeStoreNode(label, attr, value=child_store, parent=self)
        child_store.parent = node  # Dual relationship
        self.nodes[label] = node
        return node

    @property
    def root(self) -> TreeStore:
        """Get the root TreeStore of this hierarchy."""
        if self.parent is None:
            return self
        return self.parent.root

    @property
    def depth(self) -> int:
        """Get the depth of this store in the hierarchy (root=0)."""
        if self.parent is None:
            return 0
        return self.parent.parent.depth + 1 if self.parent.parent else 1

    def keys(self) -> Iterator[str]:
        """Iterate over node labels."""
        return iter(self.nodes.keys())

    def values(self) -> Iterator[TreeStoreNode]:
        """Iterate over nodes."""
        return iter(self.nodes.values())

    def items(self) -> Iterator[tuple[str, TreeStoreNode]]:
        """Iterate over (label, node) pairs."""
        return iter(self.nodes.items())

    def get(self, label: str, default: Any = None) -> TreeStoreNode | Any:
        """Get a node by label, with optional default."""
        return self.nodes.get(label, default)

    def as_dict(self) -> dict[str, Any]:
        """Convert to plain dict (recursive).

        Branch nodes become nested dicts with their attributes merged.
        Leaf nodes become their value directly.
        """
        result: dict[str, Any] = {}
        for label, node in self.nodes.items():
            if node.is_branch:
                child_dict = node.value.as_dict()
                if node.attr:
                    # Merge attributes at the same level
                    result[label] = {**node.attr, **child_dict}
                else:
                    result[label] = child_dict
            else:
                result[label] = node.value
        return result

    def walk(
        self, _prefix: str = ""
    ) -> Iterator[tuple[str, TreeStoreNode]]:
        """Iterate over all paths and nodes.

        Yields:
            Tuples of (path, node) for each node in the tree.

        Example:
            >>> for path, node in store.walk():
            ...     print(path, node.value)
        """
        for label, node in self.nodes.items():
            path = f"{_prefix}.{label}" if _prefix else label
            yield path, node
            if node.is_branch:
                yield from node.value.walk(_prefix=path)


def valid_children(*allowed: str, **constraints: str) -> Callable:
    """Decorator to specify valid children for a builder method.

    Can be used in two ways:

    1. Simple list of allowed tags:
        @valid_children('div', 'span', 'p')

    2. With cardinality constraints:
        @valid_children(div='0:', span='1:3', title='1')
        # div: 0 or more (unlimited)
        # span: 1 to 3 occurrences
        # title: exactly 1 (mandatory)

    Cardinality format: 'min:max'
        - '0:' = zero or more (optional, unlimited)
        - '1:' = one or more (mandatory, unlimited)
        - '1' or '1:1' = exactly one (mandatory)
        - '0:3' = zero to three
        - ':5' = zero to five (same as '0:5')

    Args:
        *allowed: Tag names that are valid children (implies '0:').
        **constraints: Tag names with cardinality constraints.

    Returns:
        Decorator function.

    Example:
        >>> class HtmlBuilder(TreeStoreBuilder):
        ...     @valid_children('li')
        ...     def ul(self, **attr):
        ...         return self.branch('ul', **attr)
        ...
        ...     @valid_children(href='1')  # href is mandatory
        ...     def a(self, **attr):
        ...         return self.branch('a', **attr)
    """
    def decorator(func: Callable) -> Callable:
        # Build constraints dict
        parsed: dict[str, tuple[int, int | None]] = {}

        # Simple allowed tags: default to '0:' (zero or more)
        for tag in allowed:
            parsed[tag] = (0, None)

        # Tags with explicit constraints
        for tag, constraint in constraints.items():
            parsed[tag] = _parse_cardinality(constraint)

        func._valid_children = parsed  # type: ignore
        return func

    return decorator


def _parse_cardinality(spec: str | int | bool) -> tuple[int, int | None]:
    """Parse a cardinality specification.

    Args:
        spec: Cardinality spec like '0:', '1:3', '1', True, or int.

    Returns:
        Tuple of (min, max) where max=None means unlimited.
    """
    if spec is True:
        return (0, None)
    if isinstance(spec, int):
        return (spec, spec)
    if not isinstance(spec, str):
        raise ValueError(f"Invalid cardinality spec: {spec}")

    if ':' not in spec:
        # Single number means exact count
        n = int(spec)
        return (n, n)

    parts = spec.split(':')
    min_val = int(parts[0]) if parts[0] else 0
    max_val = int(parts[1]) if parts[1] else None
    return (min_val, max_val)


class InvalidChildError(Exception):
    """Raised when an invalid child tag is used."""
    pass


class MissingChildError(Exception):
    """Raised when a mandatory child is missing."""
    pass


class TooManyChildrenError(Exception):
    """Raised when too many children of a type are added."""
    pass


class TreeStoreBuilder:
    """Base builder class for fluent TreeStore construction.

    Subclass this to create domain-specific builders (HTML, XML, etc.)
    with typed methods and validation.

    The builder maintains a current position in the tree and provides:
    - branch(): Create a branch node and descend into it
    - leaf(): Create a leaf node (stay at current level)
    - up(): Go back to parent level
    - build(): Return the constructed TreeStore

    Example:
        >>> builder = TreeStoreBuilder()
        >>> store = (builder
        ...     .branch('users')
        ...         .branch('user', id=1)
        ...             .leaf('name', 'Alice')
        ...             .leaf('email', 'alice@example.com')
        ...         .up()
        ...         .branch('user', id=2)
        ...             .leaf('name', 'Bob')
        ...         .up()
        ...     .up()
        ...     .build())
    """

    # Override in subclasses to enable free-form tag creation
    ALLOWED_TAGS: set[str] | None = None  # None = allow all

    def __init__(self) -> None:
        """Initialize the builder with an empty root TreeStore."""
        self._store = TreeStore()
        self._current = self._store
        self._tag_stack: list[str] = []  # Track current tag context
        self._child_counts: dict[int, dict[str, int]] = {}  # depth -> {tag: count}

    def branch(self, tag: str, _name: str | None = None, **attr) -> TreeStoreBuilder:
        """Create a branch node and descend into it.

        Args:
            tag: The node's tag/type.
            _name: Optional explicit name (default: auto-generated).
            **attr: Node attributes.

        Returns:
            self for method chaining.
        """
        self._validate_child(tag)
        self._increment_child_count(tag)

        # Generate label: use _name or auto-generate
        label = _name or self._generate_label(tag)

        node = self._current.add_branch(label, attr)
        node.value._tag = tag  # Store tag for validation context

        self._current = node.value
        self._tag_stack.append(tag)
        self._init_child_counts()

        return self

    def leaf(
        self, tag: str, value: Any, _name: str | None = None, **attr
    ) -> TreeStoreBuilder:
        """Create a leaf node (stay at current level).

        Args:
            tag: The node's tag/type.
            value: The node's value.
            _name: Optional explicit name (default: auto-generated).
            **attr: Node attributes.

        Returns:
            self for method chaining.
        """
        self._validate_child(tag)
        self._increment_child_count(tag)

        label = _name or self._generate_label(tag)
        self._current.add_node(label, attr, value)

        return self

    def up(self) -> TreeStoreBuilder:
        """Go back to parent level.

        Returns:
            self for method chaining.

        Raises:
            ValueError: If already at root level.
        """
        if self._current.parent is None:
            raise ValueError("Already at root level")

        # Validate mandatory children before leaving
        self._validate_mandatory_children()

        parent_node = self._current.parent
        if parent_node.parent is None:
            raise ValueError("Already at root level")

        self._current = parent_node.parent
        self._tag_stack.pop()

        return self

    def build(self) -> TreeStore:
        """Return the constructed TreeStore.

        Validates all mandatory children are present.

        Returns:
            The root TreeStore.
        """
        # Return to root and validate
        while self._current.parent is not None:
            self._validate_mandatory_children()
            parent_node = self._current.parent
            if parent_node.parent is None:
                break
            self._current = parent_node.parent
            if self._tag_stack:
                self._tag_stack.pop()

        return self._store

    def _generate_label(self, tag: str) -> str:
        """Generate a unique label for a tag.

        Uses pattern: tag_0, tag_1, tag_2, ...
        """
        existing = [
            label for label in self._current.nodes
            if label == tag or label.startswith(f"{tag}_")
        ]
        if not existing:
            return f"{tag}_0"
        return f"{tag}_{len(existing)}"

    def _get_current_tag(self) -> str | None:
        """Get the tag of the current context."""
        return self._tag_stack[-1] if self._tag_stack else None

    def _get_valid_children(self) -> dict[str, tuple[int, int | None]] | None:
        """Get valid children for the current context."""
        current_tag = self._get_current_tag()
        if current_tag is None:
            return None

        method = getattr(self, current_tag, None)
        if method is None:
            return None

        return getattr(method, '_valid_children', None)

    def _validate_child(self, tag: str) -> None:
        """Validate that a child tag is allowed in current context."""
        # Check ALLOWED_TAGS if defined
        if self.ALLOWED_TAGS is not None and tag not in self.ALLOWED_TAGS:
            raise InvalidChildError(f"Tag '{tag}' is not in ALLOWED_TAGS")

        valid = self._get_valid_children()
        if valid is None:
            return  # No constraints

        if tag not in valid:
            current = self._get_current_tag()
            raise InvalidChildError(
                f"Tag '{tag}' is not a valid child of '{current}'. "
                f"Allowed: {list(valid.keys())}"
            )

        # Check max count
        min_count, max_count = valid[tag]
        current_count = self._get_child_count(tag)
        if max_count is not None and current_count >= max_count:
            raise TooManyChildrenError(
                f"Maximum {max_count} '{tag}' children allowed, "
                f"already have {current_count}"
            )

    def _validate_mandatory_children(self) -> None:
        """Validate that all mandatory children are present."""
        valid = self._get_valid_children()
        if valid is None:
            return

        for tag, (min_count, _) in valid.items():
            if min_count > 0:
                current_count = self._get_child_count(tag)
                if current_count < min_count:
                    raise MissingChildError(
                        f"Mandatory child '{tag}' missing. "
                        f"Required: {min_count}, found: {current_count}"
                    )

    def _init_child_counts(self) -> None:
        """Initialize child counts for current depth."""
        depth = self._current.depth
        if depth not in self._child_counts:
            self._child_counts[depth] = {}

    def _get_child_count(self, tag: str) -> int:
        """Get current count of children with given tag."""
        depth = self._current.depth
        return self._child_counts.get(depth, {}).get(tag, 0)

    def _increment_child_count(self, tag: str) -> None:
        """Increment count of children with given tag."""
        depth = self._current.depth
        if depth not in self._child_counts:
            self._child_counts[depth] = {}
        self._child_counts[depth][tag] = self._child_counts[depth].get(tag, 0) + 1
