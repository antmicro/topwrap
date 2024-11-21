from dataclasses import fields
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import marshmallow_dataclass
import pytest
from marshmallow import ValidationError

from topwrap.common_serdes import (
    AnnotatedFlatTree,
    FlatTree,
    MarshmallowDataclassExtensions,
    NestedDict,
    ResourcePathT,
    annotate_flat_tree,
    ext_field,
    flatten_tree,
    unflatten_annotated_tree,
)
from topwrap.config import config
from topwrap.repo.files import IncorrectUrlException
from topwrap.resource_field import (
    FileHandler,
    InvalidArgumentException,
    InvalidIdentifierException,
    RepoHandler,
    UriHandler,
    YamlCommonSchemes,
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

    @pytest.fixture
    def annot_tree_unsorted_order(self) -> AnnotatedFlatTree[str, Any]:
        return [
            {
                "type": "required",
                "direction": "out",
                "name": "data_out",
                "width": 16,
            },
            {
                "type": "optional",
                "direction": "in",
                "name": "data_in",
                "width": 32,
            },
            {
                "type": "required",
                "direction": "out",
                "name": "valid",
                "width": 1,
            },
        ]

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

    def test_unflatten_annotated_unsorted_tree(
        self, annot_tree_unsorted_order: AnnotatedFlatTree[str, Any]
    ):
        assert unflatten_annotated_tree(
            annot_tree_unsorted_order, ["direction", "type", "name", "width"], sort=True
        ) == {
            "out": {"required": {"data_out": 16, "valid": 1}},
            "in": {"optional": {"data_in": 32}},
        }


@marshmallow_dataclass.dataclass
class DummyDataclass(MarshmallowDataclassExtensions):
    str_f: str
    int_f: int
    deep_f: Dict[Any, Any] = ext_field(dict)


class TestDataclassExtensions:
    def test_no_cleanup_regular(self):
        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            opt_field1: List[int] = ext_field(list, self_cleanup=False)
            opt_field2: List[str] = ext_field(list, self_cleanup=False)
            opt_field3: Dict[str, List[int]] = ext_field(dict, self_cleanup=False)

        serial = TestDataclass(opt_field1=[1, 2, 3, 4]).to_dict()

        assert "opt_field1" in serial and "opt_field2" in serial and "opt_field3" in serial

    def test_cleanup_regular(self):
        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            req_field: List[int]
            opt_field: List[str] = ext_field(list)
            opt_field2: List[str] = ext_field(list)
            opt_field3: List[str] = ext_field(list)
            opt_field4: Dict[int, List[str]] = ext_field(dict)

        serial = TestDataclass(req_field=[], opt_field2=[], opt_field3=["bar"]).to_dict()

        assert "req_field" in serial and "opt_field3" in serial
        assert (
            "opt_field" not in serial and "opt_field2" not in serial and "opt_field4" not in serial
        )

    def test_cleanup_deep_cleanup(self):
        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            req_field_regular: Dict[str, List[int]]
            req_field_list: List[Any] = ext_field(deep_cleanup=True)
            req_field_deepclean: Dict[str, Dict[str, List[Any]]] = ext_field(deep_cleanup=True)
            opt_field_deepclean: Dict[str, Dict[str, List[Any]]] = ext_field(
                dict, deep_cleanup=True
            )
            opt_field_deep_seq: List[Any] = ext_field(list, deep_cleanup=True)

        deep_dict = {
            "shallow_empty": {},
            "deep_full": {"empty": [], "not_empty": ["foo", {}]},
            "deep_empty": {"empty": [{}], "emptier": [{"a": []}]},
        }
        serial = TestDataclass(
            req_field_regular={"empty": []},
            req_field_list=["asdf", {}, None],
            req_field_deepclean=deep_dict,
            opt_field_deepclean=deep_dict,
            opt_field_deep_seq=["item", ["item", {}, ["item", [], {"item", tuple()}, set()]]],
        ).to_dict()

        for fld in fields(TestDataclass):
            assert fld.name in serial

        assert serial["req_field_regular"]["empty"] == []
        assert serial["req_field_list"] == ["asdf"]
        assert serial["opt_field_deep_seq"] == ["item", ["item", ["item", {"item", tuple()}]]]
        for fld in ("req_field_deepclean", "opt_field_deepclean"):
            assert "shallow_empty" not in serial[fld]
            assert "deep_empty" not in serial[fld]
            assert serial[fld]["deep_full"] == {"not_empty": ["foo"]}

    def test_noops(self):
        @marshmallow_dataclass.dataclass
        class Inner:
            fld: List[Any] = ext_field(deep_cleanup=True)

        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            req_self: Dict[Any, Any] = ext_field(self_cleanup=True)
            req_nested: Inner = ext_field(deep_cleanup=True)

        serial = TestDataclass(req_self={}, req_nested=Inner(fld=[])).to_dict()

        assert serial["req_nested"] == {"fld": []}
        assert serial["req_self"] == {}

    def test_cleanup_no_simple_type_erasure(self):
        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            opt_int_field: int = ext_field(0)
            opt_str_field: str = ext_field("")
            opt_float_field: float = ext_field(0.0)
            opt_bool_field: bool = ext_field(False)
            nested: Dict[str, Union[int, str, float, bool]] = ext_field(dict, deep_cleanup=True)

        nested = {"int": 0, "str": "", "float": 0.0, "bool": False}
        serial = TestDataclass(nested=nested).to_dict()

        for field in fields(TestDataclass):
            assert field.name in serial

        for field in nested:
            assert field in serial["nested"]

    @pytest.fixture
    def dummy_instance(self):
        return DummyDataclass(str_f="a", int_f=3, deep_f={"bar": "a"})

    def test_dict_methods(self, dummy_instance: DummyDataclass):
        data = {"str_f": "a", "int_f": 3, "deep_f": {"bar": "a"}}

        assert DummyDataclass.from_dict(data) == dummy_instance
        assert dummy_instance.to_dict() == data

    def test_yaml_methods(self, dummy_instance: DummyDataclass):
        data = "{deep_f: {bar: a}, int_f: 3, str_f: a}\n"

        assert DummyDataclass.from_yaml(data) == dummy_instance
        assert dummy_instance.to_yaml(default_flow_style=True) == data

    def test_file_methods(self, dummy_instance: DummyDataclass):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.yaml"
            dummy_instance.save(path)

            assert DummyDataclass.load(path) == dummy_instance

    def test_yaml_inlining(self):
        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            this: Tuple[str, ...] = ext_field(tuple, inline_depth=0)
            each_elem: List[Any] = ext_field(list, inline_depth=1)
            dictf: Dict[str, Any] = ext_field(dict, inline_depth=2)

        yaml = TestDataclass(
            each_elem=[(1, 2, 3), [4, 5, 6]],
            dictf={"foo": [{1: 2}]},
            this=("a", "b", "c"),
        ).to_yaml()

        assert (
            yaml
            == r"""dictf:
  foo:
  - {1: 2}
each_elem:
- [1, 2, 3]
- [4, 5, 6]
this: [a, b, c]
"""
        )

    @pytest.fixture
    def repo_in_cfg(self):
        """Temporarily add 'my_repo' repo to the config repos"""
        with TemporaryDirectory() as td:
            with open(Path(td) / "test.txt", "w") as f:
                f.write("h")

            org = config.repositories
            config.repositories = org.copy()
            config.repositories["my_repo"] = FileHandler(td)
            yield
            config.repositories = org

    def test_resource_path_field(self, repo_in_cfg: Any):
        """Tests the `ResourcePathT` field to see if the different schemes are resolved and saved correctly"""

        @marshmallow_dataclass.dataclass
        class TestDataclass(MarshmallowDataclassExtensions):
            files: list[ResourcePathT]

        data = TestDataclass.load(Path("tests/data/data_parse/test_relative_paths.yaml"))
        for res in data.files:
            res.to_path().exists()

        # Save the dataclass to a tempfile in a completely different path
        # and load it again to verify if the paths got converted correctly
        with NamedTemporaryFile() as f:
            data.save(Path(f.name))
            data = TestDataclass.load(Path(f.name))
            for res in data.files:
                assert res.to_path().exists()

        def test_err(uri: str, err: Type[Exception] = ValidationError, match: Optional[str] = None):
            with pytest.raises(err, match=match):
                TestDataclass.from_dict({"files": [uri]}).files[0].to_path().open()

        test_err("i/do/not/exist.yaml", InvalidIdentifierException, "match regex")
        test_err("dile:./file.txt", InvalidIdentifierException, "scheme: 'dile'")
        test_err("file:i/do/not/exist.yaml", FileNotFoundError)
        test_err("get:", IncorrectUrlException)
        test_err("get:foo", IncorrectUrlException)
        test_err("repo:cores/axi.txt", ValueError, "not enough values")
        test_err("repo[fake_repo]:cores/core.yaml", ValueError, "Could not find repo")

        # Test serialization
        assert FileHandler("path/to/file").to_str() == "file:path/to/file"
        assert UriHandler("https://google.com").to_str() == "get:https://google.com"
        assert RepoHandler("cores/core", ["my_repo"]).to_str() == "repo[my_repo]:cores/core"

        with pytest.raises(InvalidArgumentException):
            RepoHandler("cores/core", ["bad|args"]).to_str()

        data = TestDataclass(
            [
                FileHandler("./topwrap/resource_field.py"),
                UriHandler(
                    "https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/pyproject.toml"
                ),
                RepoHandler("test.txt", ["my_repo"]),
                YamlCommonSchemes.parse("repo[my_repo]:test.txt"),
                YamlCommonSchemes.parse("file:./topwrap/resource_field.py"),
            ]
        )

        with NamedTemporaryFile() as f:
            data.save(Path(f.name))
            data = TestDataclass.load(Path(f.name))
            for res in data.files:
                assert res.to_path().exists()
