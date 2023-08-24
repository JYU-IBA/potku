# coding=utf-8
"""
Created on 18.8.2023
Updated on 24.8.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2023 Sami Voutilainen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Sami Voutilainen"
__version__ = "2.0"

import sys
import json
import hashlib
import platform
import requests
import time
import zipfile

from pathlib import Path
from datetime import datetime
from typing import Optional
from typing import List

"""
Script for managing the external data files of Potku located primarily in
./external/share and additionally for Windows awk.exe in .external/bin. The
script has a simple terminal interface that can be used by calling the script
without arguments. The interface can be used to manage your local external files
and used to update or create an entirely new manifest file based on your local
files and the existing manifest.

This script can be ran with either no arguments to use the interactive terminal
interface, or with one extra argument 'fetch' to quickly download all the files
on the external_manifest.txt file. In the latter case only the number of failed
downloads is returned. This latter method is how this script is chained with
GitHub actions with the package_potku.yml action.

After updating the external_manifest.txt it should be committed and pushed to 
GitHub. After the manifest is pushed the new versions of files should be uploaded
to Potku Dev's Google Drive by adding a new version for existing files (and
possibly deleting previous versions) and for entirely new files the link fields
in external_manifest.txt should be manually filled with file id part of the link
you get from Google Drive by copying a share link for the file.
"""

dev_directory = Path(__file__).parent
root_directory = dev_directory.parent
share_directory = root_directory.joinpath(r"external/share")
bin_directory = root_directory.joinpath(r"external/bin")
temp_directory = root_directory.joinpath(r"external/temp")
manifest_file_path = dev_directory.joinpath(r"./external_manifest.txt")
download_retries = 3


def download_file(file_id: str, destination: Path, verbose: Optional[bool] = False) -> int:
    """
    Downloads a publicly shared file from Google Drive using the file id portion
    of a Google Drive link. File is downloaded to given path.
    Args:
        file_id: file id string of the Drive link.
        destination: absolute filepath where to save the downloaded file.
        verbose: whether to enable or disable printing
    """

    URL = f"https://drive.google.com/uc?export=download&id={file_id}"

    session = requests.Session()
    response = session.get(URL, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    if response.status_code < 400:

        destination.parent.mkdir(exist_ok=True, parents=True)
        if "awk.exe" in str(destination):
            destination = destination.parent.joinpath('awk.zip')
        with open(destination, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        if "awk.zip" in str(destination):
            with zipfile.ZipFile(destination, 'r') as zip_ref:
                zip_ref.extractall(destination.parent)
                zip_ref.close()
            destination.unlink(missing_ok=True)
    else:
        if verbose:
            print(f"{destination.name} failed to download: {response.status_code}")

    time.sleep(2)  # Sleep 2 seconds to avoid too frequent requests

    return response.status_code


def calculate_sha256(absolute_path: Path) -> str:
    """
    Calculates the sha256 hash of a file in the given path.
    Args:
        absolute_path: The absolute path to the target file.

    Return: string representation of the sha256 hash.
    """

    sha256 = hashlib.sha256()
    with open(absolute_path, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_local_manifest(git_data_list: List[dict]) -> List[dict]:
    """
    Creates a manifest for the locally found files in ./external/share dir and
    in the case of Windows awk.exe in .external/bin dir. Also copies over any
    existing links from an existing external_manifest.txt file.
    Args:
        git_data_list: list of the dictionaries that represent each file in the
            existing external_manifest.txt file.

    Returns: list of dictionaries representing a manifest formed from local
        files.
    """
    local_data_list = []
    list_of_local_files = list_share_files()

    for local_file in list_of_local_files:
        absolute_path = root_directory.joinpath(local_file)
        local_hash = calculate_sha256(absolute_path)
        local_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        local_link = "None"

        for git_entry in git_data_list:
            if git_entry["file_path"] == local_file:
                local_link = git_entry["link"]
                break

        local_dict = {
            "file_path": local_file,
            "date": local_date,
            "hash": local_hash,
            "link": local_link
        }
        local_data_list.append(local_dict)

    return local_data_list


def compare_manifests(git_manifest: List[dict], local_manifest: List[dict]) -> List[List[dict]]:
    """
    Function to compare an existing manifest on Git and a manifest formed from
    local files.
    Args:
        git_manifest: list of dictionaries representing the files synced to Git.
        local_manifest: list of dictionaries representing the local files.

    Returns: list containing three lists of dictionaries. First list represents
        files found only on Git, second list represents files found only locally
        and third list represents files that exist on both but have a mismatched
        sha256 hash.
    """
    only_on_git = []
    only_local = []
    out_of_sync = []

    for local in local_manifest:
        file_found = False
        for git in git_manifest:

            if git["file_path"] == local["file_path"]:
                file_found = True

                if git["hash"] == local["hash"]:
                    break

                out_of_sync.append(local)
        if not file_found:
            only_local.append(local)

    for git in git_manifest:
        file_found = False
        for local in local_manifest:
            if git["file_path"] == local["file_path"]:
                file_found = True
                break
        if file_found or (platform.system() != 'Windows' and 'awk.exe' in str(git["file_path"])):
            continue
        only_on_git.append(git)

    return [only_on_git, only_local, out_of_sync]


def save_manifest_file(data_list: List[dict], save_filepath: Path) -> None:
    """
    Saves a list of dictionaries to a .txt file into the given filepath.
    Args:
        data_list: list of dictionaries to be saved.
        save_filepath: filepath where to save the manifest file.
    """
    data_list = sorted(data_list, key=lambda d: d["file_path"], reverse=False)

    with open(save_filepath, "w") as file:
        for data_dict in data_list:
            data_dict["file_path"] = str(data_dict["file_path"].as_posix())
            json.dump(data_dict, file)
            file.write('\n')

    return


def read_manifest_file() -> List[dict]:
    """
    Reads a manifest file into a list of dictionaries.
    Returns: list of dictionaries representing files on the manifest.
    """
    data_list = []
    try:
        with open(manifest_file_path, "r") as file:
            for line in file:
                data_dict = json.loads(line)
                data_dict["file_path"] = Path(data_dict["file_path"])
                data_list.append(data_dict)
    except FileNotFoundError:
        return data_list

    data_list = sorted(data_list, key=lambda d: d["file_path"], reverse=False)

    return data_list


def list_share_files() -> List[Path]:
    """
    Function that returns a list of all the files found in the .external/share
    dir and any subdirectories. Additionally, seeks awk.exe in the ./external/bin
    dir on Windows systems.

    Returns: list of Path objects re
    """

    external_files = []
    directory = share_directory

    for path in directory.rglob('*'):
        if path.is_file():
            relative_path = path.relative_to(directory)
            path = Path("external/share") / relative_path
            external_files.append(path)

    if platform.system() == 'Windows':
        awk_path = root_directory.joinpath('external/bin/awk.exe')
        if awk_path.is_file():
            relative_path = awk_path.relative_to(root_directory)
            external_files.append(relative_path)

    return external_files


def fetch_files(manifest: List[dict], verbose: Optional[bool] = False) -> int:
    """
    Wrapper function for downloading all files in a list of dictionaries. The
    function checks the downloaded files' hashes against the manifest and retries
    the download again for the number of times dictated by the attribute
    download_retries. No retries for 403 forbidden or 404 not found errors. The
    files are stored in a temporary directory and moved to their final path
    after a successful download.
    Args:
        manifest: List of dictionaries representing the files on a manifest.
        verbose: whether to enable or disable printing

    Returns: number of failed downloads.
    """
    failed_downloads = 0
    for entry in manifest:
        attempts = 0
        download_success = False
        path = temp_directory.joinpath(entry["file_path"])

        while attempts < download_retries+1:

            ret = download_file(entry["link"], path, verbose)
            if ret == 404 or ret == 403:
                break
            if path.is_file():
                temp_hash = calculate_sha256(path)
                if temp_hash == entry["hash"]:
                    download_success = True
                    break

        if download_success:
            final_path = root_directory.joinpath(entry["file_path"])
            path.rename(final_path)

        if not download_success:
            failed_downloads += 1

    if verbose:
        if failed_downloads == 1:
            print(f"Failed to download one file")
        if failed_downloads > 1:
            print(f"Failed to download {failed_downloads} files.")

    return failed_downloads


def update_git_manifest(git_manifest: List[dict],
                        out_of_sync: List[dict],
                        only_local: Optional[List[dict]] = None,
                        ) -> List[dict]:
    """
    Updates an existing manifest file with local versions of out of sync files
    and possibly adds also local only files.
    Args:
        git_manifest: list of dictionaries representing the file on the Git
            synced manifest.
        out_of_sync list of dictionaries representing the files that exist both
            locally and on Git, but are out of sync.
        only_local: optional list of dictionaries representing files found only
            locally.

    Returns: the updated manifest as a list of dictionaries.
    """

    for local_entry in out_of_sync:
        for index, git_entry in enumerate(git_manifest):
            if local_entry["file_path"] == git_entry["file_path"]:
                git_manifest[index] = local_entry
                break

    if only_local is not None:
        for local_entry in only_local:
            git_manifest.append(local_entry)

    return git_manifest


def print_commands() -> None:
    """
    Helper function to print available commands.
    """
    print("Enter one of the following:")
    print("1: to fetch absent and out of sync files.")
    print("2: to update manifest file with local out of sync files.")
    print("3: to update manifest file with all local files.")
    print("4: to create an entirely new manifest file.")
    print("5: to cancel process. ")

    return


def manage_files() -> None:
    """
    Function that provides terminal interface for user to manage the external
    files and the manifest file based on simple user inputs.
    """
    git_manifest = read_manifest_file()
    local_manifest = create_local_manifest(git_manifest)
    only_on_git, only_local, out_of_sync = compare_manifests(git_manifest, local_manifest)

    if only_on_git:
        print("Only on git")
        for entry in only_on_git:
            print(entry)
        print("")
    if only_local:
        print("Only on local")
        for entry in only_local:
            print(entry)
        print("")
    if out_of_sync:
        print("Out of sync")
        for entry in out_of_sync:
            print(entry)
        print("")

    print_commands()

    input_accepted = False
    while not input_accepted:
        response = input()
        if response == "1":
            input_accepted = True
            fetch_files(out_of_sync, True)
            fetch_files(only_on_git, True)
            print("Local files synced to Git manifest.")
        elif response == "2":
            input_accepted = True
            updated_manifest = update_git_manifest(git_manifest, out_of_sync)
            save_manifest_file(updated_manifest, manifest_file_path)
            print("Remember to upload new versions of files to Drive and to "
                  "commit and push the updated manifest file.")
        elif response == "3":
            input_accepted = True
            updated_manifest = update_git_manifest(git_manifest, out_of_sync, only_local)
            save_manifest_file(updated_manifest, manifest_file_path)
            print("Remember to upload new versions of files to Drive, add "
                  "links for entirely new files and to commit and push the new "
                  "manifest file.")
        elif response == "4":
            input_accepted = True
            save_manifest_file(local_manifest, manifest_file_path)
            print("Remember to upload new versions of files to Drive, add "
                  "links for entirely new files and to commit and push the new "
                  "manifest file.")
        elif response == "5":
            input_accepted = True
            print("Operation cancelled.")
        else:
            print_commands()

    return


def quick_download() -> int:
    """
    A function to just download and overwrite all files quickly without any
    interactivity.

    Returns: the number of failed downloads.
    """

    git_manifest = read_manifest_file()
    failed_downloads = fetch_files(git_manifest, False)

    return failed_downloads


if __name__ == "__main__":

    arguments = sys.argv
    if len(arguments) > 2:
        print("Too many arguments")
    if len(arguments) == 1:
        manage_files()
    if len(arguments) == 2:
        if arguments[1].casefold() == "fetch":
            ret_val = quick_download()
            print(ret_val)
        else:
            print("Unknown argument")
