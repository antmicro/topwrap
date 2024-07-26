import logging
from dataclasses import dataclass
from typing import Dict, List, Set

import yaml
from typing_extensions import override

from topwrap.interface_grouper import standard_iface_grouper
from topwrap.repo.files import File, TemporaryFile
from topwrap.repo.resource import FileHandler, Resource
from topwrap.repo.user_repo import Core, InterfaceDescription
from topwrap.verilog_parser import VerilogModule, VerilogModuleGenerator

logger = logging.getLogger(__name__)


class VerilogFileHandler(FileHandler):
    def __init__(self, files: List[File]):
        self._files = files

    @override
    def parse(self) -> List[Resource]:
        @dataclass(frozen=True)
        class FileAwareModule:
            module: VerilogModule
            file: File

        def _get_file_list(
            modules: Dict[str, FileAwareModule], current: FileAwareModule
        ) -> Set[File]:
            files = {current.file}

            for comp in current.module.components:
                if comp not in modules:
                    logger.warning(
                        f'Dependency "{comp}" of module "{current.module.module_name}" was not found among the given source files'
                    )
                    continue
                files = files.union(_get_file_list(modules, modules[comp]))

            return files

        resources: List[Resource] = []
        modulesdict: Dict[str, FileAwareModule] = {}

        for file in self._files:
            modules = VerilogModuleGenerator().get_modules(str(file.path))

            for mod in modules:
                modulesdict[mod.module_name] = FileAwareModule(mod, file)

        for data in modulesdict.values():
            iface_grouper = standard_iface_grouper(
                hdl_filename=data.file.path, use_yosys=True, iface_deduce=True, ifaces_names=()
            )
            desc_file = TemporaryFile()
            ipcore_desc = data.module.to_ip_core_description(iface_grouper)
            ipcore_desc.save(desc_file.path)

            file_deps = _get_file_list(modulesdict, FileAwareModule(data.module, file))
            core = Core(data.module.module_name, desc_file, list(file_deps))
            resources.append(core)

        return resources


class InterfaceFileHandler(FileHandler):
    def __init__(self, files: List[File]):
        self._files = files

    @override
    def parse(self) -> List[Resource]:
        resources: List[Resource] = []
        for f in self._files:
            with open(f.path) as fd:
                data = yaml.safe_load(fd)
            name = data["name"]
            iface_desc = InterfaceDescription(name, f)
            resources.append(iface_desc)
        return resources
