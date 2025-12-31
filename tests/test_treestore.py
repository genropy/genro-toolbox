# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Tests for TreeStore, TreeStoreNode, and TreeStoreBuilder."""

import pytest

from genro_toolbox.treestore import (
    TreeStore,
    TreeStoreNode,
    TreeStoreBuilder,
    valid_children,
    InvalidChildError,
    MissingChildError,
    TooManyChildrenError,
    _parse_cardinality,
)


class TestTreeStoreNode:
    """Tests for TreeStoreNode."""

    def test_create_simple_node(self):
        """Test creating a simple node with scalar value."""
        node = TreeStoreNode('name', {'id': 1}, 'Alice')
        assert node.label == 'name'
        assert node.attr == {'id': 1}
        assert node.value == 'Alice'
        assert node.parent is None

    def test_create_node_defaults(self):
        """Test node creation with default values."""
        node = TreeStoreNode('empty')
        assert node.label == 'empty'
        assert node.attr == {}
        assert node.value is None
        assert node.parent is None

    def test_is_leaf(self):
        """Test is_leaf property for scalar values."""
        node = TreeStoreNode('name', value='Alice')
        assert node.is_leaf is True
        assert node.is_branch is False

    def test_is_branch(self):
        """Test is_branch property for TreeStore values."""
        store = TreeStore()
        node = TreeStoreNode('container', value=store)
        assert node.is_branch is True
        assert node.is_leaf is False

    def test_repr(self):
        """Test string representation."""
        node = TreeStoreNode('name', {'id': 1}, 'Alice')
        repr_str = repr(node)
        assert 'name' in repr_str
        assert 'Alice' in repr_str


class TestTreeStore:
    """Tests for TreeStore."""

    def test_create_empty_store(self):
        """Test creating an empty store."""
        store = TreeStore()
        assert len(store) == 0
        assert store.parent is None

    def test_add_node(self):
        """Test adding a node to the store."""
        store = TreeStore()
        node = store.add_node('name', {'id': 1}, 'Alice')
        assert 'name' in store
        assert store['name'] is node
        assert node.parent is store

    def test_add_branch(self):
        """Test adding a branch node."""
        store = TreeStore()
        node = store.add_branch('users', {'type': 'list'})
        assert node.is_branch
        assert isinstance(node.value, TreeStore)
        assert node.value.parent is node  # Dual relationship

    def test_iteration(self):
        """Test iterating over store."""
        store = TreeStore()
        store.add_node('a', value=1)
        store.add_node('b', value=2)
        assert list(store) == ['a', 'b']
        assert list(store.keys()) == ['a', 'b']

    def test_get_with_default(self):
        """Test get method with default value."""
        store = TreeStore()
        assert store.get('missing') is None
        assert store.get('missing', 'default') == 'default'

    def test_root_property(self):
        """Test root property navigation."""
        root = TreeStore()
        branch_node = root.add_branch('level1')
        child_store = branch_node.value
        child_node = child_store.add_branch('level2')
        grandchild_store = child_node.value

        assert root.root is root
        assert child_store.root is root
        assert grandchild_store.root is root

    def test_depth_property(self):
        """Test depth calculation."""
        root = TreeStore()
        assert root.depth == 0

        branch = root.add_branch('level1')
        assert branch.value.depth == 1

        deeper = branch.value.add_branch('level2')
        assert deeper.value.depth == 2

    def test_as_dict_simple(self):
        """Test conversion to dict with simple values."""
        store = TreeStore()
        store.add_node('name', value='Alice')
        store.add_node('age', value=30)
        assert store.as_dict() == {'name': 'Alice', 'age': 30}

    def test_as_dict_nested(self):
        """Test conversion to dict with nested branches."""
        store = TreeStore()
        user_node = store.add_branch('user', {'id': 1})
        user_node.value.add_node('name', value='Alice')
        user_node.value.add_node('email', value='alice@example.com')

        expected = {
            'user': {
                'id': 1,
                'name': 'Alice',
                'email': 'alice@example.com',
            }
        }
        assert store.as_dict() == expected

    def test_walk(self):
        """Test walking the tree."""
        store = TreeStore()
        store.add_node('a', value=1)
        branch = store.add_branch('b')
        branch.value.add_node('c', value=2)

        paths = [(path, node.label) for path, node in store.walk()]
        assert ('a', 'a') in paths
        assert ('b', 'b') in paths
        assert ('b.c', 'c') in paths


class TestParseCardinality:
    """Tests for cardinality parsing."""

    def test_parse_true(self):
        """Test parsing True (unlimited)."""
        assert _parse_cardinality(True) == (0, None)

    def test_parse_int(self):
        """Test parsing integer (exact count)."""
        assert _parse_cardinality(3) == (3, 3)

    def test_parse_exact_string(self):
        """Test parsing exact count string."""
        assert _parse_cardinality('1') == (1, 1)
        assert _parse_cardinality('5') == (5, 5)

    def test_parse_range(self):
        """Test parsing range strings."""
        assert _parse_cardinality('0:') == (0, None)
        assert _parse_cardinality('1:') == (1, None)
        assert _parse_cardinality('1:3') == (1, 3)
        assert _parse_cardinality(':5') == (0, 5)
        assert _parse_cardinality('0:10') == (0, 10)


class TestValidChildrenDecorator:
    """Tests for @valid_children decorator."""

    def test_simple_allowed_tags(self):
        """Test decorator with simple tag list."""
        @valid_children('div', 'span')
        def method():
            pass

        assert method._valid_children == {
            'div': (0, None),
            'span': (0, None),
        }

    def test_with_constraints(self):
        """Test decorator with cardinality constraints."""
        @valid_children(title='1', item='1:5')
        def method():
            pass

        assert method._valid_children == {
            'title': (1, 1),
            'item': (1, 5),
        }

    def test_mixed_args_and_kwargs(self):
        """Test decorator with both args and kwargs."""
        @valid_children('div', 'span', title='1')
        def method():
            pass

        assert method._valid_children == {
            'div': (0, None),
            'span': (0, None),
            'title': (1, 1),
        }


class TestTreeStoreBuilder:
    """Tests for TreeStoreBuilder."""

    def test_simple_build(self):
        """Test building a simple tree."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('user')
                .leaf('name', 'Alice')
                .leaf('age', 30)
            .up()
            .build())

        assert 'user_0' in store
        user = store['user_0'].value
        assert 'name_0' in user
        assert user['name_0'].value == 'Alice'
        assert user['age_0'].value == 30

    def test_nested_branches(self):
        """Test building nested branches."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('level1')
                .branch('level2')
                    .branch('level3')
                        .leaf('value', 'deep')
                    .up()
                .up()
            .up()
            .build())

        level1 = store['level1_0'].value
        level2 = level1['level2_0'].value
        level3 = level2['level3_0'].value
        assert level3['value_0'].value == 'deep'

    def test_sibling_branches(self):
        """Test building sibling branches."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('parent')
                .branch('child')
                    .leaf('name', 'first')
                .up()
                .branch('child')
                    .leaf('name', 'second')
                .up()
            .up()
            .build())

        parent = store['parent_0'].value
        assert 'child_0' in parent
        assert 'child_1' in parent
        assert parent['child_0'].value['name_0'].value == 'first'
        assert parent['child_1'].value['name_0'].value == 'second'

    def test_explicit_name(self):
        """Test using explicit names instead of auto-generated."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('user', _name='alice')
                .leaf('email', 'alice@example.com', _name='contact')
            .up()
            .build())

        assert 'alice' in store
        assert 'contact' in store['alice'].value

    def test_attributes(self):
        """Test passing attributes to nodes."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('div', id='main', class_='container')
                .leaf('text', 'Hello', style='bold')
            .up()
            .build())

        div = store['div_0']
        assert div.attr == {'id': 'main', 'class_': 'container'}
        text = div.value['text_0']
        assert text.attr == {'style': 'bold'}

    def test_up_at_root_raises(self):
        """Test that up() at root raises ValueError."""
        builder = TreeStoreBuilder()
        with pytest.raises(ValueError, match="Already at root"):
            builder.up()

    def test_build_returns_to_root(self):
        """Test that build() returns to root level."""
        builder = TreeStoreBuilder()
        store = (builder
            .branch('a')
                .branch('b')
                    .branch('c')
                        .leaf('x', 1)
            # No up() calls
            .build())

        # Should still get the root store
        assert 'a_0' in store


class TestTypedBuilder:
    """Tests for typed builders with validation."""

    def test_valid_children_enforcement(self):
        """Test that invalid children are rejected."""
        class HtmlBuilder(TreeStoreBuilder):
            @valid_children('li')
            def ul(self, **attr):
                return self.branch('ul', **attr)

            def li(self, **attr):
                return self.branch('li', **attr)

            def div(self, **attr):
                return self.branch('div', **attr)

        builder = HtmlBuilder()
        builder.ul()
        builder.li()  # OK
        builder.up()

        with pytest.raises(InvalidChildError, match="div.*not a valid child"):
            builder.div()  # Should fail

    def test_mandatory_children(self):
        """Test that mandatory children are enforced."""
        class DocBuilder(TreeStoreBuilder):
            @valid_children(title='1', body='1')
            def document(self, **attr):
                return self.branch('document', **attr)

            def title(self, text: str, **attr):
                return self.leaf('title', text, **attr)

            def body(self, **attr):
                return self.branch('body', **attr)

        builder = DocBuilder()
        builder.document()
        builder.title('My Doc')
        # Missing body

        with pytest.raises(MissingChildError, match="body.*missing"):
            builder.up()

    def test_max_children_enforcement(self):
        """Test that max children count is enforced."""
        class LimitedBuilder(TreeStoreBuilder):
            @valid_children(item='0:2')
            def container(self, **attr):
                return self.branch('container', **attr)

            def item(self, value: str, **attr):
                return self.leaf('item', value, **attr)

        builder = LimitedBuilder()
        builder.container()
        builder.item('first')
        builder.item('second')

        with pytest.raises(TooManyChildrenError, match="Maximum 2"):
            builder.item('third')

    def test_allowed_tags_whitelist(self):
        """Test ALLOWED_TAGS whitelist."""
        class RestrictedBuilder(TreeStoreBuilder):
            ALLOWED_TAGS = {'div', 'span', 'p'}

        builder = RestrictedBuilder()
        builder.branch('div')  # OK
        builder.up()

        with pytest.raises(InvalidChildError, match="not in ALLOWED_TAGS"):
            builder.branch('script')
