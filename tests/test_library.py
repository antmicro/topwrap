# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from topwrap import library
from topwrap.backend.yaml.backend import DesignDescriptionBackend
from topwrap.config import _resolve_library_uris
from topwrap.frontend.yaml.design import (
    DesignDescriptionFrontend,
    DesignDescriptionFrontendException,
)
from topwrap.frontend.yaml.design_schema import DesignDescription
from topwrap.library import (
    _INDEX_CACHE,
    TOPWRAP_INTERFACE_FILE_TYPE,
    TOPWRAP_MODULE_FILE_TYPE,
    LibraryError,
    _fusesoc_library,
    _identify,
    _indexes,
    _is_remote_uri,
    _LibraryRegistration,
    _split_git_ref,
    _vlnv_matches,
    fusesoc_core_of,
    interface_index,
    library_contents,
    library_core_of,
    list_libraries,
    module_index,
)
from topwrap.plugin.pipeline import BuildPipeline
from topwrap.util import get_config


def _minimal_module_yaml(name: str) -> str:
    """The smallest valid IP module description, under a fresh name."""
    return rf"""
id:
  vendor: example.com
  library: demo
  name: {name}
signals:
  in:
    - {{name: clk}}
"""


def _minimal_core_file(vlnv: str) -> str:
    """A CAPI2 .core marking ``module.yaml`` next to it as a topwrapModule."""
    return rf"""CAPI=2:

name : {vlnv}

filesets:
  topwrap:
    files:
        - module.yaml : {{ file_type : topwrapModule }}
"""


@pytest.fixture
def isolated_libraries():
    """Keep registered libraries and the VLNV index out of other tests."""
    original = dict(get_config().libraries)
    yield
    get_config().libraries.clear()
    get_config().libraries.update(original)
    library.clear_index_cache()


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


def _make_demo_source_repo(src: Path) -> None:
    """A git repo providing one module, tagged ``v1`` at its first commit."""
    src.mkdir()
    _git("init", "-q", cwd=src)
    _git("config", "user.email", "test@example.com", cwd=src)
    _git("config", "user.name", "Test", cwd=src)

    core = src / "demo_core"
    core.mkdir()
    (core / "module.yaml").write_text(
        r"""
id:
  vendor: example.com
  library: demo
  name: demo_core
signals:
  in:
    - {name: clk}
"""
    )
    (core / "demo.core").write_text(
        r"""CAPI=2:

name : example.com:demo:demo_core

filesets:
  topwrap:
    files:
        - module.yaml : { file_type : topwrapModule }
"""
    )
    _git("add", "-A", cwd=src)
    _git("commit", "-q", "-m", "initial", cwd=src)
    _git("tag", "v1", cwd=src)


def _add_rst_signal(src: Path) -> None:
    """Advance the source repo with a second commit, past the ``v1`` tag."""
    module = src / "demo_core" / "module.yaml"
    module.write_text(module.read_text() + "  out:\n    - {name: rst}\n")
    _git("add", "-A", cwd=src)
    _git("commit", "-q", "-m", "add rst", cwd=src)


class TestSplitGitRef:
    @pytest.mark.parametrize(
        ("uri", "expected"),
        [
            ("https://github.com/a/b.git", ("https://github.com/a/b.git", None)),
            ("git@github.com:a/b.git", ("git@github.com:a/b.git", None)),
            ("https://github.com/a/b.git@main", ("https://github.com/a/b.git", "main")),
            ("git@github.com:a/b.git@v1", ("git@github.com:a/b.git", "v1")),
            ("ssh://git@host/a/b.git@v2", ("ssh://git@host/a/b.git", "v2")),
        ],
    )
    def test_ref_is_split_off_the_path(self, uri: str, expected: tuple[str, str | None]):
        assert _split_git_ref(uri) == expected

    @pytest.mark.parametrize(
        ("uri", "expected"),
        [
            (
                "https://oauth2:TOKEN@gitlab.com/a/b.git",
                ("https://oauth2:TOKEN@gitlab.com/a/b.git", None),
            ),
            (
                "https://user@github.com/a/b.git",
                ("https://user@github.com/a/b.git", None),
            ),
            (
                "https://oauth2:TOKEN@gitlab.com/a/b.git@main",
                ("https://oauth2:TOKEN@gitlab.com/a/b.git", "main"),
            ),
        ],
    )
    def test_userinfo_is_not_a_ref(self, uri: str, expected: tuple[str, str | None]):
        """Credentials survive, ref or no ref."""
        assert _split_git_ref(uri) == expected


class TestVlnvMatches:
    KEY = "antmicro.com:topwrap-interfaces:axi4:0.1"

    @pytest.mark.parametrize(
        "query",
        [
            "axi4",
            "topwrap-interfaces:axi4",
            "antmicro.com:topwrap-interfaces:axi4",
            "antmicro.com:topwrap-interfaces:axi4:0.1",
            ":topwrap-interfaces:axi4",
            "::axi4",
        ],
    )
    def test_partial_queries_match(self, query: str):
        assert _vlnv_matches(self.KEY, query)

    @pytest.mark.parametrize(
        "query",
        [
            "axi3",
            "other.com:topwrap-interfaces:axi4",
            "antmicro.com:other-library:axi4",
            "antmicro.com:topwrap-interfaces:axi4:9.9",
        ],
    )
    def test_mismatching_queries_do_not_match(self, query: str):
        assert not _vlnv_matches(self.KEY, query)


class TestIdentify:
    def test_mapping_id_becomes_a_vlnv(self, tmp_path: Path):
        path = tmp_path / "iface.yaml"
        path.write_text(yaml.safe_dump({"id": {"vendor": "a.com", "library": "l", "name": "n"}}))
        assert _identify(path) == "a.com:l:n:0.1"

    def test_string_id_is_kept(self, tmp_path: Path):
        path = tmp_path / "iface.yaml"
        path.write_text(yaml.safe_dump({"id": "a.com:l:n:2.0"}))
        assert _identify(path) == "a.com:l:n:2.0"

    def test_unreadable_file_falls_back_to_its_name(self, tmp_path: Path):
        path = tmp_path / "broken.yaml"
        path.write_text("{ not: valid: yaml")
        assert _identify(path) == "broken.yaml"


class TestBuiltinLibrary:
    """The builtin library is registered by default and needs no network."""

    def test_interfaces_are_indexed(self):
        assert interface_index(), "the builtin library should provide interfaces"

    def test_provides_no_modules(self):
        """Builtin only ships interfaces; IP cores live with the examples that use them."""
        assert module_index() == {}

    def test_every_indexed_interface_file_exists(self):
        for path in interface_index().values():
            assert path.is_file()

    def test_contents_are_sorted_and_disjoint(self):
        name, uri = next(iter(list_libraries().items()))
        modules, interfaces = library_contents(name, uri)
        assert modules == sorted(modules)
        assert interfaces == sorted(interfaces)
        assert not set(modules) & set(interfaces)


class TestResolveLibraryUris:
    def test_relative_directory_is_made_absolute(self, tmp_path: Path):
        (tmp_path / "cores").mkdir()
        resolved = _resolve_library_uris({"lib": "cores"}, tmp_path)
        assert resolved["lib"] == str((tmp_path / "cores").resolve())

    def test_directory_containing_an_at_sign_is_resolved(self, tmp_path: Path):
        name = "cores@v2"
        (tmp_path / name).mkdir()
        resolved = _resolve_library_uris({"lib": name}, tmp_path)
        assert resolved["lib"] == str((tmp_path / name).resolve())

    @pytest.mark.parametrize(
        "uri",
        ["https://github.com/a/b.git", "git@github.com:a/b.git", "does/not/exist"],
    )
    def test_non_directories_are_left_alone(self, uri: str, tmp_path: Path):
        assert _resolve_library_uris({"lib": uri}, tmp_path)["lib"] == uri


class TestDesignDeclaredLibraries:
    @pytest.fixture
    def scoped_library_designs(self, tmp_path: Path) -> tuple[Path, Path]:
        cores = tmp_path / "cores"
        cores.mkdir()
        (cores / "module.yaml").write_text(_minimal_module_yaml("scoped_core"))
        (cores / "scoped.core").write_text(_minimal_core_file("example.com:demo:scoped_core"))

        declared = tmp_path / "declared.yaml"
        declared.write_text(
            "config: {libraries: {demo: ./cores}}\nips: {instance: {core: scoped_core}}\n"
        )
        undeclared = tmp_path / "undeclared.yaml"
        undeclared.write_text("ips: {instance: {core: scoped_core}}\n")
        return declared, undeclared

    def test_relative_path_resolves_against_the_design_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """A design's `config: libraries:` must not depend on the cwd."""
        cores = tmp_path / "cores"
        cores.mkdir()
        (cores / "module.yaml").write_text(_minimal_module_yaml("demo_fifo"))
        (cores / "demo_fifo.core").write_text(_minimal_core_file("example.com:demo:demo_fifo"))
        design = tmp_path / "project.yaml"
        design.write_text(
            r"""
name: cfg_lib_demo
config:
  libraries:
    demo_cores: ./cores
ips:
  fifo:
    core: demo_fifo
"""
        )

        # Build from somewhere else entirely; "./cores" must still be found.
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        des, _ = DesignDescriptionFrontend().parse_file(design)
        assert [c.name for c in des.components] == ["fifo"]

    def test_library_does_not_leak_to_a_later_parse(
        self, scoped_library_designs: tuple[Path, Path], isolated_libraries: None
    ):
        declared, undeclared = scoped_library_designs

        DesignDescriptionFrontend().parse_file(declared)
        with pytest.raises(DesignDescriptionFrontendException, match="no module matches"):
            DesignDescriptionFrontend().parse_file(undeclared)

    def test_library_does_not_leak_from_pipeline_preparation(
        self, scoped_library_designs: tuple[Path, Path], isolated_libraries: None
    ):
        declared, undeclared = scoped_library_designs
        original_libraries = dict(get_config().libraries)

        BuildPipeline.yaml_sv_pipeline().prepare_files([], declared)
        assert get_config().libraries == original_libraries

        with pytest.raises(DesignDescriptionFrontendException, match="no module matches"):
            BuildPipeline.yaml_sv_pipeline().prepare_files([], undeclared)


class TestCoreAndFileAreMutuallyExclusive:
    def test_neither_set_is_rejected(self):
        with pytest.raises(Exception, match="exactly one of 'file' or 'core'"):
            DesignDescription.from_yaml(
                r"""
ips:
  x: {}
"""
            )

    def test_both_set_is_rejected(self):
        with pytest.raises(Exception, match="exactly one of 'file' or 'core'"):
            DesignDescription.from_yaml(
                r"""
ips:
  x:
    file: foo.yaml
    core: bar
"""
            )


class TestCoreReferenceRoundTrip:
    def test_module_and_fusesoc_core_vlnvs_are_distinct(
        self, tmp_path: Path, isolated_libraries: None
    ):
        cores = tmp_path / "cores"
        cores.mkdir()
        module = cores / "module.yaml"
        module.write_text(_minimal_module_yaml("adapter_ip"))
        (cores / "container.core").write_text(_minimal_core_file("example.com:demo:container:1.0"))
        get_config().libraries["demo"] = str(cores)
        library.clear_index_cache()

        assert library_core_of(module) == "example.com:demo:adapter_ip:0.1"
        assert fusesoc_core_of(module) == "example.com:demo:container:1.0"

    def test_a_library_module_is_written_back_as_core(
        self, tmp_path: Path, isolated_libraries: None
    ):
        """Must not come back as a file path."""
        cores = tmp_path / "cores"
        cores.mkdir()
        (cores / "module.yaml").write_text(_minimal_module_yaml("adapter_ip"))
        (cores / "adapter_ip.core").write_text(_minimal_core_file("example.com:demo:adapter_ip"))
        get_config().libraries["demo"] = str(cores)
        library.clear_index_cache()

        design, _ = DesignDescriptionFrontend().parse_str(
            r"""
name: rt
ips:
  adapter:
    core: adapter_ip
"""
        )
        backend = DesignDescriptionBackend()
        content = next(backend.serialize(backend.represent(design.parent))).content

        assert "core: example.com:demo:adapter_ip:0.1" in content
        assert "file:" not in content

    def test_a_plain_file_reference_stays_a_file_reference(self, tmp_path: Path):
        module = tmp_path / "outside.yaml"
        module.write_text(_minimal_module_yaml("outside_fifo"))
        design = tmp_path / "project.yaml"
        design.write_text(
            rf"""
name: rt
ips:
  fifo:
    file: {module}
"""
        )

        des, _ = DesignDescriptionFrontend().parse_file(design)
        backend = DesignDescriptionBackend()
        content = next(backend.serialize(backend.represent(des.parent))).content

        assert "core:" not in content
        assert "outside.yaml" in content


class TestUnreadableLibrary:
    def test_a_missing_local_path_is_not_treated_as_a_clone(self, tmp_path: Path):
        with pytest.raises(LibraryError, match="not a directory"):
            _fusesoc_library("gone", str(tmp_path / "no_such_dir"))

    @pytest.mark.parametrize(
        ("uri", "remote"),
        [
            ("https://github.com/a/b.git", True),
            ("ssh://host/a/b.git", True),
            ("git@github.com:a/b.git", True),
            ("./cores", False),
            ("/opt/cores", False),
            ("cores", False),
        ],
    )
    def test_remote_is_decided_by_shape(self, uri: str, remote: bool):
        assert _is_remote_uri(uri) is remote

    def test_an_unreadable_library_is_skipped_and_not_memoized(self, tmp_path: Path):
        """Must not be remembered as empty."""
        missing = tmp_path / "later"
        libs = (_LibraryRegistration("later", str(missing)),)

        indexes = _indexes(libs)
        assert indexes.modules == {}
        assert indexes.interfaces == {}
        assert libs not in _INDEX_CACHE, "a failed read must not be cached"

        # The library shows up; the earlier failure must not mask it.
        missing.mkdir()
        (missing / "m.yaml").write_text(
            r"""
id:
  vendor: a.com
  library: l
  name: n
"""
        )
        (missing / "m.core").write_text(
            r"""CAPI=2:

name : a.com:l:n

filesets:
  t:
    files:
        - m.yaml : { file_type : topwrapModule }
"""
        )
        assert "a.com:l:n:0.1" in _indexes(libs).modules

    @pytest.mark.parametrize("name", ["../escape", "nested/name", ".", ""])
    def test_invalid_library_name_is_rejected(self, name: str, tmp_path: Path):
        with pytest.raises(LibraryError, match="invalid library name"):
            library.add_library(name, str(tmp_path))

    def test_duplicate_full_vlnv_is_rejected(self, tmp_path: Path, isolated_libraries: None):
        libraries = []
        for name in ("first", "second"):
            root = tmp_path / name
            root.mkdir()
            (root / "module.yaml").write_text(_minimal_module_yaml("duplicate"))
            (root / f"{name}.core").write_text(_minimal_core_file(f"example.com:{name}:container"))
            libraries.append(_LibraryRegistration(name, str(root)))

        with pytest.raises(LibraryError, match="duplicate VLNV.*example.com:demo:duplicate:0.1"):
            _indexes(tuple(libraries))


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
class TestGitLibrary:
    """Exercises the git branch of add_library / update_libraries /
    library_status against a real repository, not just string parsing."""

    @pytest.fixture
    def git_source(self, tmp_path: Path) -> Path:
        src = tmp_path / "src"
        _make_demo_source_repo(src)
        return src

    def test_add_clones_and_checks_out_a_pinned_ref(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        uri = f"file://{git_source}@v1"

        library.add_library("demo", uri)

        checkout = library.LIBRARY_CHECKOUT_DIR / "demo" / "demo_core" / "module.yaml"
        assert checkout.is_file()
        assert "example.com:demo:demo_core:0.1" in library.module_index()
        assert library.library_status("demo", uri) == "v1"

    def test_update_on_a_pinned_ref_does_not_move(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        uri = f"file://{git_source}@v1"
        library.add_library("demo", uri)
        checkout = library.LIBRARY_CHECKOUT_DIR / "demo" / "demo_core" / "module.yaml"

        _add_rst_signal(git_source)
        updated = library.update_libraries(("demo",))

        assert updated == ["demo"]
        assert "rst" not in checkout.read_text()

    def test_update_on_an_unpinned_library_pulls_new_commits(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        uri = f"file://{git_source}"
        library.add_library("demo", uri)
        checkout = library.LIBRARY_CHECKOUT_DIR / "demo" / "demo_core" / "module.yaml"
        assert "rst" not in checkout.read_text()

        _add_rst_signal(git_source)
        updated = library.update_libraries()

        assert updated == ["demo"]
        assert "rst" in checkout.read_text()
        assert library.library_status("demo", uri) is not None

    def test_checkout_root_is_created_and_gitignored(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        assert not library.LIBRARY_CHECKOUT_DIR.exists()

        library.add_library("demo", f"file://{git_source}")

        assert (library.LIBRARY_CHECKOUT_DIR / ".gitignore").read_text() == "*\n"

    def test_local_directory_library_has_no_status(self, tmp_path: Path, isolated_libraries: None):
        local = tmp_path / "cores"
        local.mkdir()
        assert library.library_status("demo", str(local)) is None

    def test_git_library_not_yet_checked_out_has_no_status(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        assert library.library_status("demo", f"file://{git_source}") is None

    def test_existing_checkout_from_another_remote_is_rejected(
        self,
        tmp_path: Path,
        git_source: Path,
        isolated_libraries: None,
        monkeypatch: pytest.MonkeyPatch,
    ):
        other_source = tmp_path / "other"
        _make_demo_source_repo(other_source)
        monkeypatch.chdir(tmp_path)
        library.add_library("demo", f"file://{git_source}")

        with pytest.raises(LibraryError, match="belongs to"):
            library._fusesoc_library("demo", f"file://{other_source}")


class TestFileTypeConstants:
    def test_builtin_interface_cores_use_the_interface_file_type(self):
        """Marks its YAML as an interface, not a module."""
        core_dir = Path(__file__).parent.parent / "topwrap" / "builtin" / "interfaces"
        cores = list(core_dir.glob("*.core"))
        assert cores, "expected builtin interface .core files"
        for core in cores:
            text = core.read_text()
            assert TOPWRAP_INTERFACE_FILE_TYPE in text
            assert TOPWRAP_MODULE_FILE_TYPE not in text
