# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from typing_extensions import override

logger = logging.getLogger(__name__)

FileContent = Union[str, bytes, bytearray]


class File(ABC):
    """Base class for files obtained through different access methods.
    It describes a common interface needed for storing information about files
    in user's repository.
    """

    @abstractmethod
    def copy(self, dst: Path) -> None:
        """Copies the file to a given destination"""

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

    @override
    def copy(self, dst: Path) -> None:
        dst = Path(dst)
        if dst.exists():
            raise FileExistsError(f"Cannot copy a file to {dst}. The file already exists")
        dst.write_bytes(self._path.read_bytes())


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

    @override
    def copy(self, dst: Path):
        if dst.exists():
            raise FileExistsError(f"Cannot copy a file to {dst}. The file already exists")
        dst.write_bytes(self._path.read_bytes())


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

    @lru_cache(maxsize=None)
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
            f"GetHttpFile.download: Downloaded the file from {self.url} and saved in {download_path}"
        )

        return download_path

    @override
    def copy(self, dst: Path) -> None:
        if dst.exists():
            raise FileExistsError(f"Cannot copy a file to {dst}. The file already exists")

        dst.write_bytes(self.path.read_bytes())

    @property
    @override
    def path(self) -> Path:
        return self.download()
