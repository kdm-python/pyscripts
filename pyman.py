#!/bin/python3

"""
PyMan

Bring up help, functions, or definition file conveniently in the command line

--- TODO ---

1) -m: Display help for builtins like enumerate, currently only working for modules

2) -d: Also display data variables e.g. string.ascii as well as classes and functions

3) -sc: Error getting file path, return stderr from subprocess
        TypeError exception from inspect.getfile() if not file found
        TypeError: <module 'sys' (built-in)> is a built-in module
        Catch above and print message if it is inbuilt in C and not module
        Eventually also locate the C code for builtins and try to open that
        
4) -sc: Use vim options to jump to the line with member in if one is there: activate /<member> command in vim

5) -doc: If module.member, find and highlight first occurrence of member name on module doc page: JS script?

6) -i: Interative menu -i to loop over search, open man page then come back to program

7) Advanced: Find a way to set up tab autocomplete

"""

import sys
import argparse
import pkgutil
import importlib
import subprocess
import inspect
from types import ModuleType
import webbrowser
import http.client
import urllib.parse
from pathlib import Path
from typing import Any, Callable

def import_module(module_name: str) -> ModuleType | None:  # Return type for module?
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError:
        print(f"Module '{module_name}' not found.\n")

def module_partial_results(module_name) -> None:
    partial_results = module_partial_search(module_name)
    if len(partial_results) > 0:
        print("Possible suggestions:")
        for m in partial_results:
            print(f"* {m}")
        sys.exit()
    else:
        print("No matches found")
        sys.exit()

def member_partial_results(module: ModuleType | None, member_name: str) -> None:
    partial_results = member_partial_search(module, member_name)
    if len(partial_results) > 0:
        print("Possible suggestions:")
        for m in partial_results:
            print(f"* {m}")
        sys.exit()
    else:
        print("No matches found")
        sys.exit()

def get_module_functions(module_name: str, include_dunder: bool = False) -> list[str] | None:  # -> list[Callable]:
    # Import should be done first and object passed to here or the man page function
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as err:
        print(err)
        module_partial_results(module_name)
        # Could return an empty list instead?
    else:
        attributes = dir(module)
        functions = [
            getattr(module, attr).__name__ for attr in attributes 
            if callable(getattr(module, attr))
            
        ]
        if not include_dunder:
            functions = [func for func in functions if not func.startswith("_")]
            
        return functions

def print_module_members(module_name: str) -> None:
    members = get_module_functions(module_name)
    if members:
        for mem in members:
            print(f"* {mem}")
    
def get_modules() -> list:
    module_list = [x.name for x in list(pkgutil.iter_modules()) if not x.name.startswith("_")]
    return module_list

def get_builtins() -> list:
    return [x for x in dir(__builtins__) if not x.startswith("_")]

def module_partial_search(search_term: str) -> list[str]:
    mods = get_modules()
    builtin = get_builtins()
    all_members = mods + builtin
    matches = [m for m in all_members if m.startswith(search_term)]
    return matches

def member_partial_search(module: ModuleType | None, search_term: str) -> list[str]:
    # Simply search dir(module) list and do above
    matches = [m for m in dir(module) if m.startswith(search_term)]
    return matches

def search_all(search_term: str) -> str | None:
    mods = get_modules()
    builtin = get_builtins()
    if search_term in mods:
        return "module"
    elif search_term in builtin:
        return "builtin"
    if len(module_partial_search(search_term)) > 0:
        print("Possible suggestions:")
        results = module_partial_search(search_term)
        for m in results:
            print(m)
        return "partial"        

# --manual

def member_help(parts: list[str]) -> None:
    module = import_module(parts[0])

    # Initialize attribute with the base module
    attribute = module
    for part in parts[1:]:
        try:
            attribute = getattr(attribute, part)
        except AttributeError:  # Not getting attribute error
            print(f"{parts[1]} not found as a member of {parts[0]}")
            member_partial_results(module, parts[1] )  # Call help on the final attribute
    help(attribute) 
    sys.exit()
    
def module_help(module_name: str) -> None:
    module = import_module(module_name)
    if module is None:
        module_partial_results(module_name)
    else:
        help(module)
    sys.exit(0)

def builtin_help(builtin_name: str) -> None:
    """
    TODO: Handle builtins like enumerate
    """

def get_inputs(arg: str) -> tuple[str, str | None]:
    if arg == "":
        print("Please provide a full or partial module name")
        sys.exit()
    elif (".") in arg:
        module, member = arg.split(".")
    else:
        module, member = arg, None
    return module, member

def process_input(parts: tuple):
    # Possibly try returning a function instead
    if parts[1] is not None:
        member_help(list(parts))
    else:
        module_help(parts[0])

# --sourcecode

def open_file_source(module_name: str, editor: str ="vim"):
    module = import_module(module_name)
    try:
        file_path = Path(inspect.getfile(module))
    except TypeError:
        # print(f"Can't open source for builtins yet.\n{err}")
        print(f"Can't find source file for {module_name}")
    except NameError as err:
        print(f"Error: module not found in local namespace.\n{err}")
    else:
        # TODO: Custom editor choice
        # Must open in read only in all
        subprocess.run(["view", file_path])
        # Print stderr if file path not found
        # If the member parts value is not None, auto run /<member> when vim opens
        sys.exit()

# --doc

def check_docs_url(url: str):
    parsed_url = urllib.parse.urlparse(url)
    conn = http.client.HTTPSConnection(parsed_url.netloc)
    conn.request("HEAD", parsed_url.path)
    response = conn.getresponse()

    return response.status

def open_docs_page(module_name: str) -> None:
    """
    TODO: Jump to highlighted definition of a single function within the docs: 
    Run ctrl-f in the browser somehow?
    """
    results = search_all(module_name)
    if not results:
        print("No matches found.")
        sys.exit()
    elif results == "partial":
        sys.exit()
    else:
        url = f"https://docs.python.org/3/library/{module_name}.html"
        # If URL = 404 response, don't open
        try:
            status = check_docs_url(url)
            if status == 200:
                webbrowser.open(url)
            elif status == 404:
                print(f"No documentation found for {module_name}")
            else:
                print(f"Received unexpected status code {status} for URL: {url}")
        except Exception as e:
            print(f"Error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(prog="PyMan")
    parser.add_argument("module", help="The module or function to be accessed.")
    parser.add_argument("-m", "--manual", 
                        action="store_true",
                        help="Runs help(module) to open the man page.")
    parser.add_argument("-d", "--dir", 
                        action="store_true",
                        help="Runs dir(module) to see list of available members of this module.")
    parser.add_argument("-doc", "--documentation",  
                        action="store_true",
                        help="Open official docs page in browser if one exists.")
    parser.add_argument("-sc", "--sourcecode", 
                        help="Open source file for module or function in vim.",
                        action="store_true")
    
    # TODO: Must differentiate between module argument being a builtin function instead,
    # since results and logic will be different

    args = vars(parser.parse_args())
    module, member = get_inputs(args["module"])
    
    if args["manual"] is True:
        process_input((module, member))
        sys.exit()
    if args["dir"] is True:
        print_module_members(module)
        sys.exit()
    if args["documentation"] is True:
        open_docs_page(module)
        sys.exit()
    if args["sourcecode"] is True:
        open_file_source(module)
        sys.exit()

    # No options, default to manual
    process_input((module, member))

if __name__ == "__main__":
    main()
