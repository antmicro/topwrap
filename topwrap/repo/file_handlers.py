from typing import List

import yaml
from typing_extensions import override

from topwrap.interface_grouper import standard_iface_grouper
from topwrap.repo.files import File, TemporaryFile
from topwrap.repo.resource import FileHandler, Resource
from topwrap.repo.user_repo import Core, InterfaceDescription
from topwrap.verilog_parser import VerilogModuleGenerator


class VerilogFileHandler(FileHandler):
    def __init__(self, files: List[File]):
        self._files = files

    @override
    def parse(self) -> List[Resource]:
        resources: List[Resource] = []
        for file in self._files:
            modules = VerilogModuleGenerator().get_modules(str(file.path))
            iface_grouper = standard_iface_grouper(
                hdl_filename=file.path, use_yosys=True, iface_deduce=True, ifaces_names=()
            )
            for module in modules:
                desc_file = TemporaryFile()
                ipcore_desc = module.to_ip_core_description(iface_grouper)
                ipcore_desc.save(desc_file.path)

                core = Core(module.module_name, desc_file, [file])
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
