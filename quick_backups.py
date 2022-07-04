from dataclasses import dataclass
import os
from pathlib import Path
import shutil
from typing import Any, TypedDict
import yaml


class SourcePathDict(TypedDict):
    path: str
    is_folder: bool
    exceptions: list[str]


@dataclass
class SourcePath:
    name: str
    path: Path
    is_dir: bool
    exceptions: list[str]

    @staticmethod
    def build_dict(config_dict: dict[Any, Any]):
        dict_of_objs: dict[str, SourcePath] = {}
        for name, attribs in config_dict["source paths"].items():
            attribs: SourcePathDict
            dict_of_objs[name] = SourcePath(
                name=name,
                path=Path(attribs["path"]),
                is_dir=attribs["is_folder"],
                exceptions=attribs["exceptions"],
            )
        return dict_of_objs


@dataclass
class Configuration:
    source_paths: dict[str, SourcePath]
    backup_path: Path

    @staticmethod
    def build(config_path: str):
        with open(Path(config_path), "r") as f:
            config_dict = yaml.safe_load(f)

        return Configuration(
            source_paths=SourcePath.build_dict(config_dict),
            backup_path=Path(config_dict["backup path"]),
        )


def backup_file(src_file: Path, dest_file: Path):
    print(f"Source:{src_file}\nDestination:{dest_file}")
    # if old file exists, EXPUNGE
    if os.path.isfile(dest_file):
        print(f"delete old backup {dest_file}")
        os.remove(dest_file)
    elif os.path.isdir(dest_file):
        print(f"delete old backup {dest_file}")
        shutil.rmtree(dest_file)

    # copy each file to the destination
    try:
        if os.path.isdir(src_file):
            func = shutil.copytree
        else:
            func = shutil.copy
        func(src_file, dest_file)
        return True
    except PermissionError as err:
        print(f"  Failed, {err}! File may be locked/in use.")
        return False


def backup_folder(folder_path: SourcePath, backup_path: Path):
    path = folder_path.path
    for filename in os.listdir(path):
        if filename in folder_path.exceptions:
            print(f"Skipping {filename}")
            continue
        src_file = Path.joinpath(path, filename)
        dest_file = Path.joinpath(backup_path, filename)
        if backup_file(src_file, dest_file):
            print(f"  copied {src_file} to dest: {backup_path}")


def backup_source_path(source_path: SourcePath, backup_path: Path):
    if source_path.is_dir:
        backup_folder(source_path, backup_path)
    else:
        backup_file(
            source_path.path,
            Path.joinpath(backup_path, source_path.path.name),
        )


def main():
    config = Configuration.build("config.yaml")

    print("#### QUICK BACKUPS ####")

    for name, source_path in config.source_paths.items():
        print(f"\n## Backing up {name} ##")
        backup_source_path(source_path, config.backup_path)

    print("\n#### SUCCESS! ####")


if __name__ == "__main__":
    main()
