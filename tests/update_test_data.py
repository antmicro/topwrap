from pathlib import Path

import click
from tests_kpm.common import TEST_DATA_PATH, save_file_to_json
from tests_kpm.conftest import Dict, all_designs_data, test_dirs_data

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


def all_examples_designs_data() -> Dict[str, DesignDescription]:
    examples = {}
    for dir in (Path(TEST_DATA_PATH) / "examples").iterdir():
        examples[dir.name] = DesignDescription.load(Path(f"examples/{dir.name}/project.yaml"))
    return examples


def update_dataflows():
    test_dirs = test_dirs_data()
    for example_name, design in all_designs_data().items():
        spec = ipcore_yamls_to_kpm_spec([], design)
        dataflow = kpm_dataflow_from_design_descr(design, spec)
        save_file_to_json(
            test_dirs[example_name],
            f"dataflow_{example_name}.json",
            dataflow,
        )


def update_specifications():
    test_dirs = test_dirs_data()
    for example_name, design in all_designs_data().items():
        specification = ipcore_yamls_to_kpm_spec([], design)
        save_file_to_json(
            test_dirs[example_name],
            f"specification_{example_name}.json",
            specification,
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
@click.option(
    "--design",
    default=False,
    is_flag=True,
    help="Update all designs",
)
def update_test_data(dataflow: bool, specification: bool, design: bool):
    if dataflow:
        update_dataflows()

    if specification:
        update_specifications()


if __name__ == "__main__":
    update_test_data()
