from pathlib import Path

import click
from tests_kpm.common import TEST_DATA_PATH, save_file_to_json
from tests_kpm.conftest import Dict, List, all_yaml_files_data, test_dirs_data

from topwrap.design import DesignDescription
from topwrap.design_to_kpm_dataflow_parser import kpm_dataflow_from_design_descr
from topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec


def all_examples_designs_data() -> Dict[str, DesignDescription]:
    examples = {}
    for dir in (Path(TEST_DATA_PATH) / "examples").iterdir():
        examples[dir.name] = DesignDescription.load(Path(f"examples/{dir.name}/project.yml"))
    return examples


def update_dataflows(
    all_yaml_files: Dict[str, List[str]], all_examples_designs: Dict[str, DesignDescription]
):
    for example_name, example_design in all_examples_designs.items():
        spec = ipcore_yamls_to_kpm_spec(all_yaml_files[example_name])
        dataflow = kpm_dataflow_from_design_descr(example_design, spec)
        save_file_to_json(
            Path(TEST_DATA_PATH) / "examples" / example_name,
            f"dataflow_{example_name}.json",
            dataflow,
        )


def update_specifications(all_yaml_files: Dict[str, List[str]]):
    test_dirs = test_dirs_data()
    for example_name, yamlfiles in all_yaml_files.items():
        specification = ipcore_yamls_to_kpm_spec(yamlfiles)
        save_file_to_json(
            test_dirs[example_name],
            f"specification_{example_name}.json",
            specification,
        )


def update_designs(all_examples_designs: Dict[str, DesignDescription]):
    def change_ips_path(design: DesignDescription, example_name: str):
        ips_path = Path("topwrap/ips/")
        example_path = Path(f"examples/{example_name}")
        topwrap_ips = ["axi"]

        for hier_design in design.design.hierarchies.values():
            change_ips_path(hier_design, example_name)

        for design_ip in design.ips.values():
            file_path = Path(design_ip.file)
            if str(file_path.parent) in topwrap_ips:
                design_ip.file = str(Path(ips_path / file_path))
            else:
                design_ip.file = str(Path(example_path / file_path))

    for example_name, example_design in all_examples_designs.items():
        change_ips_path(example_design, example_name)
        example_design.save(
            Path(TEST_DATA_PATH) / "examples" / example_name / f"project_{example_name}.yml"
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
        update_dataflows(all_yaml_files_data(), all_examples_designs_data())

    if specification:
        update_specifications(all_yaml_files_data())

    if design:
        update_designs(all_examples_designs_data())


if __name__ == "__main__":
    update_test_data()
