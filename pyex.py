#!/bin/python3

from collections import namedtuple
import argparse
import os
import stat
import sys
import shutil
from pathlib import Path
from typing import Callable

"""
Pyex: Manage making files executable anywhere in the shell
"""

SCRIPTS_DIR = "/home/kyle/bin/"

SHEBANGS = {
    ".py": "#!/bin/python3",
    ".sh": "#!/bin/bash"
    # .c => trigget compile before moving
}

class FileExtensionError(Exception):
    pass

FileStatus = namedtuple("FileStatus", "suffix shebang exec")

# --- TODO ---
# Write shebang line to the file
# Make sure it works with files that already don't have a suffix
# Find a way to work out if a file without a suffix is py or sh, by scanning the code
# --customname Custom file name
# --keepsuffix Allow skipping of the suffix remove
# Executable: Allow setting user, group and global 

def get_file_text(suffix: str, script_path: str) -> str:
    path = Path(script_path)
    if path.suffix != suffix:
        raise FileExtensionError(f"The file does not have a {suffix} suffix.")

    file_text = path.read_text()
    
    return file_text

def get_file_status(script_path: str) -> FileStatus:
    suffix = Path(script_path).suffix
    lines = get_file_text(suffix, script_path).split("\n")
    shebang = True if lines[0] in SHEBANGS.values() else False
    executable = True if os.access(script_path, os.X_OK) else False
    file_status =  FileStatus(suffix, shebang, executable)

    return file_status

def add_shebang(file_text: str, suffix: str) -> list[str]:
    assert suffix in list(SHEBANGS.keys()), "An invalid suffix was received by the add_shebang() function"
    lines = file_text.split("\n")

    shebang_line = SHEBANGS[suffix]
    if lines[0] == shebang_line:
        print("File already has correct shebang")
        # Return original lines unchanged
        return lines
    
    new_lines = [shebang_line, ""]
    new_line_list = new_lines + lines

    # TODO: Write file and replace original
    
    return new_line_list

def make_executable(script_path: str, which_exec: dict = {}) -> int:
    """
    TODO: Add options to have choice of user/group/global/all, could be dict of bools
    """
    if not os.path.exists(script_path):
        # This should not ever occur, because file exist determined outside in main functions
        raise FileNotFoundError("Specified file path does not exist")
    if os.access(script_path, os.X_OK):
        print("File is already executable.")
        return 1
    st = os.stat(script_path)
    try:
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    except Exception as e:
        print(f"Error making file executable:\n{e}")
        return 1
    return 0

def remove_suffix(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix == "":
        print("File already has no suffix")
        # Return unchanged
        return file_path
    
    path = path.rename(path.with_suffix(""))
    return str(path)

def compile_c_file(file_path: str) -> None:
    ...

def copy_file(
    file_path: str,
    destination_path: str, 
) -> int:
    try:
        shutil.copy(file_path, destination_path)
        return 0
    except FileNotFoundError:
        # For testing purposes, may not need later since check is done beforehand
        print(f"Source file {file_path} not found.")
        return 1
    except PermissionError:
        print(f"Permission denied: unable to move {file_path}.")
        return 1
    except Exception as e:
        print(f"An error occurred while moving the file: {e}")
        return 1

def make_temp_file(file_path: str) -> Path | int:
    original_path = Path(file_path)
    
    temp_file_name = "." + original_path.name
    temp_file_path = original_path.with_name(temp_file_name)
    
    copy_result = copy_file(str(original_path), str(temp_file_path))
    if copy_result != 0:
        print("* Error copying file *")
        return 1
    else:
        return temp_file_path

def build_final_path(path: str, custom_name: str | None = None) -> Path:
    if not custom_name:
        return Path(path)
    head, _ = os.path.split(path)
    return Path(os.path.join(head, custom_name))

def run_operations(file_path: str, custom_name: str | None = None):
    temp_file_path = make_temp_file(file_path)
    if temp_file_path == 0:
        print("* Error creating temp file for editing *")
        sys.exit(1)
    file_status = get_file_status(str(temp_file_path))
    file_text = get_file_text(file_status.suffix, str(temp_file_path))
    
    if file_status.exec is False:
        print("Making file executable...")
        make_executable(str(temp_file_path))
    else:
        print("File already executable, skipping...")
    
    new_lines = None
    if file_status.shebang is False:
        try:
            new_lines = add_shebang(file_text, file_status.suffix)
        except AssertionError as e:
            print(e)
            sys.exit(0)
        else:
            print("No shebang found, adding...")
    else:
        print("File already has a shebang, skipping...")
    
    # TODO: This should also work for files without a suffix

    if file_status.suffix in [x for x in SHEBANGS.keys()]: 
        print(f"Removing {temp_file_path.suffix} suffix...")
        temp_file_path = Path(remove_suffix(str(temp_file_path)))
        new_file_name = temp_file_path.name.lstrip(".")
        
        # TODO: Refactor and split all this into smaller functions
        combined_file_path = Path(SCRIPTS_DIR) / new_file_name
        final_file_path = build_final_path(str(combined_file_path), custom_name)
        shutil.copy(str(temp_file_path), str(final_file_path))
        
        if new_lines:
            final_file_path.write_text("\n".join(new_lines))
        os.remove(str(temp_file_path))
        sys.exit(0)
    else:
        print(f"{file_status.suffix} files are not currently supported.")

def main():
    parser = argparse.ArgumentParser(
        prog="PyEx", 
        description="Automate making Bash and Python scripts ready for execution anywhere."
    )

    parser.add_argument("filepath", help="the path of the target script file.")
    parser.add_argument("-a", "--all", action="store_true", help="make executable, check shebang, remove suffix and copy to bin directory.")
    parser.add_argument("-k", "--keepsuffix", action="store_true", help="keep the suffix of the file instead of removing it.")   # TODO: Integrate the custom file path into the main functions
    parser.add_argument("-c", "--customname", type=str, help="An optional custom destination file name.")
    
    args = parser.parse_args()
    if not os.path.exists(args.filepath):
        # So this check actually not needed in other functions?
        print("Specified file path does not exist")
        sys.exit(1)
    if Path(args.filepath).suffix not in list(SHEBANGS.keys()):
        print(f"'{Path(args.filepath).suffix}' is an invalid suffix, must be one of these: {list(SHEBANGS.keys())}.")
        sys.exit(1)
    if args.all:
        run_operations(args.filepath, args.customname)
    
    # TODO: Run each part in turn, allow choice of any parts
    # Will need to split run_operations()

if __name__ == "__main__":
    main()
