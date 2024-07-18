# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


import pytest

from topwrap.repo.files import TemporaryFile
from topwrap.repo.repo import Repo, ResourceNotSupportedException
from topwrap.repo.resource import FileHandler, Resource, ResourceHandler


class MySupportedResource(Resource):
    pass


class MyUnsupportedResource(Resource):
    pass


class MyFileHandler(FileHandler):
    resource_type = Resource

    def __init__(self, files):
        self._files = files

    @property
    def files(self):
        return self._files

    def parse(self):
        return [MySupportedResource()]


class MyWrongFileHandler(FileHandler):
    resource_type = Resource

    def __init__(self, files):
        self._files = files

    @property
    def files(self):
        return self._files

    def parse(self):
        return [MyUnsupportedResource()]


class MySupportedResourceHandler(ResourceHandler):
    resource_type = MySupportedResource

    def save(self, resource, repo_path):
        pass

    def load(self, repo_path):
        return []


class MyRepo(Repo):
    def __init__(self):
        resource_handlers = [MySupportedResourceHandler()]
        super().__init__(resource_handlers)


class TestRepoBase:
    @pytest.fixture()
    def repo(self):
        return MyRepo()

    @pytest.mark.usefixtures("fs")
    def test_save_supported_resource(self, repo):
        files = MyFileHandler([TemporaryFile()])
        repo.add_files(files)
        repo.save("repo")

    @pytest.mark.usefixtures("fs")
    def test_save_unsupported_resource(self, repo):
        repo.add_files(MyWrongFileHandler([TemporaryFile()]))
        with pytest.raises(ResourceNotSupportedException):
            repo.save("repo")
