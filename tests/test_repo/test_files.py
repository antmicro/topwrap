# Copyright (c 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import filecmp
import os
import urllib.parse
from pathlib import Path

import pytest

from topwrap.repo.files import HttpGetFile, LocalFile, TemporaryFile


class TestFile:
    @pytest.fixture
    def create_file(self):
        # A lambda is used instead of creating the file directly, because it
        # introduces problems when the fake filesystem from pyfakefs is used
        # in a test hierarchy. In that case, the files lifetime is not correctly
        # managed. For hierarchical tests inherited by children, we should use
        # lambdas to call the fakefs directly in the parent's scope.
        return lambda: None

    def skip_for_base_class(self):
        if type(self) == TestFile:  # noqa: E721
            pytest.skip("Skipped for base class")

    @pytest.mark.usefixtures("fs")
    def test_path_property(self, create_file):
        self.skip_for_base_class()

        file = create_file()
        assert file.path.exists(), "The path property does not point to an existing local file"

    def test_copy(self, fs, create_file):
        self.skip_for_base_class()

        file = create_file()
        EXISTING_FILE_NAME = "existing_file.txt"
        fs.create_file(EXISTING_FILE_NAME)
        with pytest.raises(FileExistsError):
            file.copy(EXISTING_FILE_NAME)

        DEST_DIR_NAME = "dest_dir"
        DEST_FILE_NAME = "dest_file.txt"
        fs.create_dir(DEST_DIR_NAME)
        dst = Path(DEST_DIR_NAME, DEST_FILE_NAME)
        file.copy(dst)
        assert dst.exists(), "The copied file hasn't been created"

        assert filecmp.cmp(
            file.path, Path(DEST_DIR_NAME, DEST_FILE_NAME), shallow=False
        ), "The copied files don't have the same content as the original file"


class TestTemporaryFile(TestFile):
    @pytest.fixture()
    def create_file(self):
        return lambda: TemporaryFile()

    @pytest.fixture()
    def str_content(self):
        return "My string content"

    @pytest.fixture()
    def byte_content(self):
        return b"My Content"

    @pytest.fixture()
    def bytearray_content(self):
        return bytearray(b"My bytearray content")

    @pytest.mark.usefixtures("fs")
    def test_create_file_without_content(self):
        file = TemporaryFile()
        assert file.path.exists(), "The temporary file hasn't been created"
        read_content = file.path.read_text()
        assert read_content == "", "The file should be empty"

    @pytest.mark.usefixtures("fs")
    def test_create_file_with_string_content(self, str_content):
        file = TemporaryFile(str_content)
        assert file.path.exists(), "The temporary file hasn't been created"
        read_content = file.path.read_text()
        assert read_content == str_content, "The file does not have expected content"

    @pytest.mark.usefixtures("fs")
    def test_create_file_with_byte_content(self, byte_content, bytearray_content):
        file = TemporaryFile(byte_content)
        assert file.path.exists(), "The temporary file hasn't been created"
        read_content = file.path.read_bytes()
        assert read_content == byte_content, "The file does not have expected content"

        file = TemporaryFile(bytearray_content)
        assert file.path.exists(), "The temporary file hasn't been created"
        read_content = file.path.read_bytes()
        assert (
            bytearray(read_content) == bytearray_content
        ), "The file does not have expected content"

    @pytest.mark.usefixtures("fs")
    def test_set_content_for_string(self, str_content):
        file = TemporaryFile(2 * str_content)
        file.set_content(str_content)
        read_content = file.path.read_text()
        assert read_content == str_content, "The file does not have expected content"

    @pytest.mark.usefixtures("fs")
    def test_set_content_for_bytes(self, byte_content, bytearray_content):
        file = TemporaryFile(2 * byte_content)

        file.set_content(byte_content)
        read_content = file.path.read_bytes()
        assert read_content == byte_content, "The file does not have expected content"

        file.set_content(bytearray_content)
        read_content = file.path.read_bytes()
        assert (
            bytearray(read_content) == bytearray_content
        ), "The file does not have expected content"

    @pytest.mark.usefixtures("fs")
    def test_deleting_files(self):
        file = TemporaryFile()
        file_path = file.path
        del file
        os.sync()
        assert not file_path.exists(), "The file still exists, but it should be removed"


class TestLocalFile(TestFile):
    @pytest.fixture()
    def create_file(self, fs):
        return lambda: LocalFile(fs.create_file("myfile.v").path)

    @pytest.mark.usefixtures("fs")
    def test_using_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            LocalFile("non_existing_file.txt")

    def test_using_existing_file(self, fs):
        file_path = Path(fs.create_file("existing_file.txt").path)
        local_file = LocalFile(file_path)
        assert local_file.path == file_path, "The file has an incorrect path"


def mock_urlretrieve(url: str, file_name: str):
    with open(file_name, "w") as fp:
        fp.write("example content")

    os.sync()
    return (file_name, "fake headers")


class TestHttpGetFile(TestFile):
    @pytest.fixture()
    def correct_url(self):
        return "https://raw.githubusercontent.com/account/repo/master/module.v"

    @pytest.fixture()
    def create_file(self, fs, monkeypatch, correct_url):
        monkeypatch.setattr(urllib.request, "urlretrieve", mock_urlretrieve)
        return lambda: HttpGetFile(correct_url)

    @pytest.mark.usefixtures("fs")
    def test_wrong_url(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlretrieve", mock_urlretrieve)
        with pytest.raises(Exception, match=r"Url .* doesn't seem to have a correct path.*"):
            HttpGetFile("wrong url")

    def test_download_dir(self, fs, monkeypatch, correct_url):
        DOWNLOAD_DIR = "download_dir"
        fs.create_dir(DOWNLOAD_DIR)
        download_dir = Path(DOWNLOAD_DIR)

        http_file = HttpGetFile(correct_url, download_dir)
        monkeypatch.setattr(urllib.request, "urlretrieve", mock_urlretrieve)
        http_file.download()
        output_path = download_dir / "module.v"
        assert output_path.exists(), "The file hasn't been created"
