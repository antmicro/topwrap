# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from pathlib import Path
from typing import Iterator, List

import pytest
from typing_extensions import override

from topwrap.repo.exceptions import (
    ResourceExistsException,
    ResourceNotFoundException,
    ResourceNotSupportedException,
)
from topwrap.repo.files import TemporaryFile
from topwrap.repo.repo import Repo
from topwrap.repo.resource import (
    FileHandler,
    Resource,
    ResourceHandler,
)
from topwrap.util import ExistsStrategy


class MySupportedResource(Resource):
    pass


class MyUnsupportedResource(Resource):
    pass


class MyFileHandler(FileHandler):
    resource_type = Resource

    @property
    def files(self):
        return self._files

    def parse(self) -> List[Resource]:
        return [MySupportedResource("resource")]


class MyWrongFileHandler(FileHandler):
    resource_type = Resource

    @property
    def files(self):
        return self._files

    def parse(self) -> List[Resource]:
        return [MyUnsupportedResource("wrong_resource")]


class MySupportedResourceHandler(ResourceHandler[MySupportedResource]):
    resource_type = MySupportedResource

    @override
    def save(
        self,
        res: MySupportedResource,
        repo_path: Path,
    ):
        repo_path.mkdir(exist_ok=True)
        (repo_path / res.name).write_text("resource")

    @override
    def load(self, repo_path: Path) -> Iterator[MySupportedResource]:
        return (MySupportedResource(p.name) for p in repo_path.iterdir())


class MyRepo(Repo):
    def __init__(self):
        resource_handlers: List[ResourceHandler[Resource]] = [MySupportedResourceHandler()]
        super().__init__(resource_handlers, "")


class TestRepoBase:
    @pytest.fixture()
    def repo(self):
        return MyRepo()

    @pytest.mark.usefixtures("fs")
    def test_save_supported_resource(self, repo: MyRepo):
        files = MyFileHandler([TemporaryFile()])
        repo.add_files(files)
        repo.save(Path("repo"))

    @pytest.mark.usefixtures("fs")
    def test_save_unsupported_resource(self, repo: MyRepo):
        with pytest.raises(ResourceNotSupportedException):
            repo.add_files(MyWrongFileHandler([TemporaryFile()]))
            repo.save(Path("repo"))

    @pytest.mark.usefixtures("fs")
    def test_repo_load(self, repo: MyRepo):
        files = MyFileHandler([TemporaryFile()])
        repo.add_files(files)
        repo.save(Path("repo"))
        repo = MyRepo()
        repo.load(Path("repo"))
        assert len(repo.get_resources(MySupportedResource)) == 1

    @pytest.mark.usefixtures("fs")
    def test_add_same_resource_two_times(self, repo: MyRepo):
        resource = MySupportedResource("resource")
        repo.add_resource(resource)

        with pytest.raises(ResourceExistsException):
            repo.add_resource(resource)

        repo.add_resource(MySupportedResource("resource"), ExistsStrategy.SKIP)
        assert repo.get_resource(MySupportedResource, "resource") is resource

        repo.add_resource(MySupportedResource("resource"), ExistsStrategy.OVERWRITE)
        assert repo.get_resource(MySupportedResource, "resource") is not resource

    @pytest.mark.usefixtures("fs")
    def test_remove_resource(self, repo: MyRepo):
        resource = MySupportedResource("supported_resource")
        repo.add_resource(resource)
        repo.remove_resource(resource)
        assert len(repo.get_resources(type(resource))) == 0
        with pytest.raises(ResourceNotSupportedException):
            repo.remove_resource(MyUnsupportedResource(""))

    @pytest.mark.usefixtures("fs")
    def test_remove_not_existing_resource(self, repo: MyRepo):
        with pytest.raises(ResourceNotFoundException):
            resource = MySupportedResource("resource")
            repo.remove_resource(resource)

    def test_get_resource(self, repo: MyRepo):
        resc = MySupportedResource("resc")
        repo.add_resource(resc)
        assert repo.get_resource(MySupportedResource, "resc") is resc
        assert resc in repo.get_resources(MySupportedResource)

    def test_get_resource_not_found(self, repo: MyRepo):
        with pytest.raises(ResourceNotSupportedException):
            repo.get_resource(MyUnsupportedResource, "")
        with pytest.raises(ResourceNotFoundException):
            repo.get_resource(MySupportedResource, "nothere")
