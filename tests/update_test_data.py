import click
from tests_kpm.conftest import all_design_paths, test_dirs_data

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.util import save_file_to_json


def update_dataflows():
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        [design_module] = frontend.parse_files([design])

        backend = KpmBackend(depth=-1)
        repr = backend.represent(design_module)

        save_file_to_json(
            test_dirs[example_name],
            f"dataflow_{example_name}.json",
            repr.dataflow,
        )


def update_specifications():
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        [design_module] = frontend.parse_files([design])

        spec = KpmSpecificationBackend.default()
        spec.add_module(design_module, recursive=True)
        spec = spec.build()

        save_file_to_json(
            test_dirs[example_name],
            f"specification_{example_name}.json",
            spec,
        )


@click.command()
@click.option(
    "--dataflow",
    default=False,
    is_flag=True,
    help="Update all dataflows",
)
@click.option(
    "--specification",
    default=False,
    is_flag=True,
    help="Update all specifications",
)
def update_test_data(dataflow: bool, specification: bool):
    if dataflow:
        update_dataflows()

    if specification:
        update_specifications()


if __name__ == "__main__":
    update_test_data()
