from typing import Any, List

import pytest

from topwrap.common_serdes import (
    AnnotatedFlatTree,
    FlatTree,
    NestedDict,
    annotate_flat_tree,
    flatten_tree,
    unflatten_annotated_tree,
)


class TestCommonSerdes:
    @pytest.fixture
    def tree_varlength(self) -> NestedDict[str, Any]:
        return {
            "a": "foo",
            "b": {"bar": 1, "baz": 2, "foobar": [1, 2, 3], "foobaz": {"i": 3, "j": 4, "k": 5}},
        }

    @pytest.fixture
    def flat_tree_varlength(self) -> FlatTree[Any]:
        return [
            ("a", "foo"),
            ("b", "bar", 1),
            ("b", "baz", 2),
            ("b", "foobar", [1, 2, 3]),
            ("b", "foobaz", "i", 3),
            ("b", "foobaz", "j", 4),
            ("b", "foobaz", "k", 5),
        ]

    @pytest.fixture
    def tree_samelength(self) -> NestedDict[str, Any]:
        return {
            "in": {
                "clk": 1,
                "rst": 1,
                "data_in": 32,
            },
            "out": {
                "data_out": 16,
                "valid": [1, 2, 3],
            },
        }

    @pytest.fixture
    def flat_tree_samelength(self) -> FlatTree[Any]:
        return [
            ("in", "clk", 1),
            ("in", "rst", 1),
            ("in", "data_in", 32),
            ("out", "data_out", 16),
            ("out", "valid", [1, 2, 3]),
        ]

    @pytest.fixture
    def tree_entries(self) -> List[str]:
        return ["direction", "name", "width"]

    @pytest.fixture
    def annot_tree(self) -> AnnotatedFlatTree[str, Any]:
        return [
            {
                "direction": "in",
                "name": "clk",
                "width": 1,
            },
            {
                "direction": "in",
                "name": "rst",
                "width": 1,
            },
            {
                "direction": "in",
                "name": "data_in",
                "width": 32,
            },
            {
                "direction": "out",
                "name": "data_out",
                "width": 16,
            },
            {
                "direction": "out",
                "name": "valid",
                "width": [1, 2, 3],
            },
        ]

    @pytest.fixture
    def annot_tree_multiple_leaves(self) -> AnnotatedFlatTree[str, Any]:
        return [
            {
                "type": "required",
                "direction": "in",
                "name": "clk",
                "width": 1,
            },
            {
                "type": "required",
                "direction": "in",
                "name": "data_in",
                "width": 32,
            },
            {
                "type": "required",
                "direction": "out",
                "name": "data_out",
                "width": 16,
            },
            {
                "type": "optional",
                "direction": "out",
                "name": "valid",
                "width": 1,
            },
            {
                "type": "optional",
                "direction": "out",
                "name": "valid",
                "width": 15,
            },
        ]

    @pytest.fixture
    def tree_multiple_leaves(self) -> NestedDict[str, Any]:
        return {
            "required": {
                "out": {
                    "data_out": 16,
                },
                "in": {
                    "clk": 1,
                    "data_in": 32,
                },
            },
            "optional": {
                "out": {
                    "valid": [1, 15],
                },
            },
        }

    @pytest.fixture
    def tree_multiple_leaves_nodir(self) -> NestedDict[str, Any]:
        return {
            "required": {
                "clk": 1,
                "data_in": 32,
                "data_out": 16,
            },
            "optional": {
                "valid": [1, 15],
            },
        }

    @pytest.fixture
    def tree_multiple_leaves_entries(self) -> List[str]:
        return ["type", "direction", "name", "width"]

    def test_flatten_tree(
        self,
        tree_samelength: NestedDict[str, Any],
        tree_varlength: NestedDict[str, Any],
        flat_tree_samelength: FlatTree[Any],
        flat_tree_varlength: FlatTree[Any],
    ):
        assert flatten_tree(tree_samelength) == flat_tree_samelength
        assert flatten_tree(tree_varlength) == flat_tree_varlength
        assert flatten_tree({}) == []

    def test_annotate_flat_tree(
        self,
        flat_tree_samelength: FlatTree[Any],
        tree_entries: List[str],
        annot_tree: AnnotatedFlatTree[str, Any],
    ):
        assert annotate_flat_tree(flat_tree_samelength, tree_entries) == annot_tree

        with pytest.raises(ValueError):
            annotate_flat_tree(flat_tree_samelength, tree_entries + ["foo"])
        with pytest.raises(ValueError):
            annotate_flat_tree(flat_tree_samelength, tree_entries[1:])

        assert annotate_flat_tree([], []) == []
        assert annotate_flat_tree([(), ()], []) == [{}, {}]

    def test_unflatten_annotated_tree(
        self,
        annot_tree: AnnotatedFlatTree[str, Any],
        tree_samelength: NestedDict[str, Any],
        tree_entries: List[str],
        annot_tree_multiple_leaves: AnnotatedFlatTree[str, Any],
        tree_multiple_leaves: NestedDict[str, Any],
        tree_multiple_leaves_entries: List[str],
        tree_multiple_leaves_nodir: NestedDict[str, Any],
    ):
        assert unflatten_annotated_tree(annot_tree, tree_entries) == tree_samelength

        assert (
            unflatten_annotated_tree(annot_tree_multiple_leaves, tree_multiple_leaves_entries)
            == tree_multiple_leaves
        )

        tree_multiple_leaves_entries.remove("direction")
        assert (
            unflatten_annotated_tree(annot_tree_multiple_leaves, tree_multiple_leaves_entries)
            == tree_multiple_leaves_nodir
        )

    def test_unflatten_flattened_identity(
        self,
        annot_tree: AnnotatedFlatTree[str, Any],
        tree_samelength: NestedDict[str, Any],
        tree_entries: List[str],
    ):
        assert (
            unflatten_annotated_tree(
                annotate_flat_tree(flatten_tree(tree_samelength), tree_entries), tree_entries
            )
            == tree_samelength
        )
