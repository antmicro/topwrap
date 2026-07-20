# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from typing_extensions import override

from topwrap.util import ExistsStrategy

logger = logging.getLogger(__name__)

FileContent = Union[str, bytes, bytearray]


class File(ABC):
    """Base class for files obtained through different access methods.
    It describes a common interface needed for storing information about files
    in user's repository.
    """

    def copy(self, dst: Path, exists_strategy: ExistsStrategy = ExistsStrategy.RAISE) -> None:
        """Copies the file to a given destination"""

        if dst.exists():
            if exists_strategy is ExistsStrategy.RAISE:
                raise FileExistsError(f"Cannot copy a file to {dst}. The file already exists")
            elif exists_strategy is ExistsStrategy.SKIP:
                return
        shutil.copy(self.path, dst)

    @property
    @abstractmethod
    def path(self) -> Path:
        """Returns a path to the file on hard drive"""


class TemporaryFile(File):
    """Holds information in a temporary file.
    Useful for saving files generated in the user repo creation process.
    """

    def __init__(self, content: Optional[FileContent] = None) -> None:
        self._fd, path = tempfile.mkstemp()
        self._path = Path(path)
        if content is not None:
            self.set_content(content)

    def set_content(self, new_content: FileContent) -> None:
        """Sets new content of the temporary file"""
        with open(self._path, "wb") as f:
            if isinstance(new_content, str):
                f.write(new_content.encode())
            else:
                f.write(new_content)

    def __del__(self) -> None:
        os.close(self._fd)
        os.remove(self._path)
        logger.debug(f"TemporaryFile.__del__: Removed the temporary {self._path} file")

    @property
    @override
    def path(self) -> Path:
        return self._path


class LocalFile(File):
    """Holds information about local files"""

    def __init__(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError(f"{path} does not exist or is not a file")
        self._path = path

    @property
    @override
    def path(self) -> Path:
        return self._path


class DownloadException(Exception):
    """Raised when there are problems with downloading data"""


class IncorrectUrlException(Exception):
    """Raised when the provided url is wrong"""


class HttpGetFile(File):
    """Holds information about files obtained using GET request"""

    def __init__(
        self,
        url: str,
        download_dir: Optional[Path] = None,
        clean_on_del: Optional[bool] = None,
    ) -> None:
        if download_dir is not None:
            self.download_dir = Path(download_dir)
            self._clean_on_del = False
        else:
            self.download_dir = Path(tempfile.mkdtemp())
            self._clean_on_del = True

        if clean_on_del is not None:
            self._clean_on_del = clean_on_del

        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.netloc or not parsed_url.path:
            raise IncorrectUrlException(
                f"Url {url} doesn't seem to have a correct path to resource"
            )
        self.url = url

    def __del__(self) -> None:
        if self._clean_on_del:
            try:
                shutil.rmtree(self.download_dir)
                logger.debug(
                    f"GetHttpFile.__del__: Removed temporary {self.download_dir} directory"
                )
            except Exception:
                logger.warning(
                    f"GetHttpFile.__del__: Couldn't remove temporary {self.download_dir} directory"
                )

    @lru_cache(maxsize=None)  # noqa: B019
    def download(self) -> Path:
        """Downloads the file using GET request.
        Because it is cached, the file will be downloaded only once"""

        parsed_url = urllib.parse.urlparse(self.url)
        file_name = Path(parsed_url.path).name
        output_path = Path(self.download_dir, file_name)

        if output_path.exists():
            raise FileExistsError(f"{output_path} already exists")

        self.download_dir.mkdir(parents=True, exist_ok=True)

        try:
            (file_path, headers) = urllib.request.urlretrieve(self.url, output_path)
        except Exception as exc:
            raise DownloadException(f"Unable to download the file from {self.url}") from exc

        download_path = Path(file_path)
        logger.debug(
            f"GetHttpFile.download: Downloaded the file from {self.url}"
            f" and saved in {download_path}"
        )

        return download_path

    @property
    @override
    def path(self) -> Path:
        return self.download()


class GitCloneException(Exception):
    """Raised when there are problems with cloning a git repository"""


DEFAULT_GIT_CACHE_DIR = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.local/cache")).expanduser() / "topwrap/git_repos"
)


class GitRepoFile(File):
    """Holds information about a directory obtained by cloning a git repository.

    Clones are cached persistently (keyed by url + ref) under
    `DEFAULT_GIT_CACHE_DIR`, so a repository is only cloned once across
    multiple runs.
    """

    _SHA_REGEX = re.compile(r"^[0-9a-fA-F]{7,40}$")

    def __init__(
        self,
        url: str,
        ref: Optional[str] = None,
        subdir: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.netloc or not parsed_url.path:
            raise IncorrectUrlException(
                f"Url {url} doesn't seem to have a correct path to resource"
            )
        self.url = url
        self.ref = ref
        self.subdir = subdir
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DEFAULT_GIT_CACHE_DIR

    @property
    def _clone_dir(self) -> Path:
        key = f"{self.url}@{self.ref or 'HEAD'}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / digest

    def _run_git(self, clone_dir: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(clone_dir), *args], check=True, capture_output=True, text=True
        )

    def clone(self) -> Path:
        """Clones (or fetches+checks out) the repository if it isn't already
        cached, returning the local directory the repository was cloned
        into."""

        clone_dir = self._clone_dir
        if (clone_dir / ".git").exists():
            logger.debug(f"GitRepoFile.clone: Using cached clone of {self.url} at {clone_dir}")
            return clone_dir

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp_dir = Path(tempfile.mkdtemp(dir=self.cache_dir))

        try:
            self._run_git(tmp_dir, "init")
            self._run_git(tmp_dir, "remote", "add", "origin", self.url)
            if self.ref is not None and self._SHA_REGEX.fullmatch(self.ref):
                self._run_git(tmp_dir, "fetch", "origin")
                self._run_git(tmp_dir, "checkout", self.ref)
            else:
                self._run_git(tmp_dir, "fetch", "--depth=1", "origin", self.ref or "HEAD")
                self._run_git(tmp_dir, "checkout", "FETCH_HEAD")
        except FileNotFoundError as exc:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise GitCloneException(
                "The 'git' executable was not found. Loading repositories via the 'git:' "
                "scheme requires git to be installed and available on the PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise GitCloneException(
                f"Unable to clone git repository from {self.url}"
                f"{f' at ref {self.ref}' if self.ref else ''}: {exc.stderr}"
            ) from exc

        if (clone_dir / ".git").exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        else:
            tmp_dir.rename(clone_dir)

        logger.debug(f"GitRepoFile.clone: Cloned {self.url} into {clone_dir}")
        return clone_dir

    @property
    @override
    def path(self) -> Path:
        repo_dir = self.clone()
        if self.subdir is None:
            return repo_dir

        sub_path = repo_dir / self.subdir
        if not sub_path.is_dir():
            raise FileNotFoundError(
                f"Subdirectory '{self.subdir}' does not exist in repository {self.url}"
            )
        return sub_path
