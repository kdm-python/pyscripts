#!/usr/bin/env python3

"""
Recipes
-------

A collection of helpful commands for various linux topics.

"""

import subprocess
import sys
import logging
import argparse
from pathlib import Path

USER = "kyle"
DIR = Path(f"/home/{USER}/.recipes/")
EDITOR = "vim"

def init(dir_path: Path = DIR) -> None:
    if not dir_path.exists():
        Path.mkdir(dir_path)
        print(f"No data directory was found, creting new at {str(DIR)}")


def edit_recipe(recipe_name: str, editor_command: str = EDITOR) -> None:
    recipe_path = DIR / f"{recipe_name}.txt"
    if not recipe_path.exists():
        print(f"No recipe called '{recipe_name}' was found.")
        return
    subprocess.run([editor_command, recipe_path])


def make_recipe(recipe_name: str, edit: bool = False, dir_path: Path = DIR) -> None:
    recipe_path = dir_path / f"{recipe_name}.txt"
    if recipe_path.exists():
        confirm = input(f"'{recipe_name}' file exists. Overwrite? Y/n ")
        if confirm != "Y":
            return
    Path.touch(recipe_path)  # Create an empty file
    if edit:  # Edit if optional arg supplied
        edit_recipe(recipe_name)


def view_recipe(recipe_name: str) -> None:
    recipe_path = DIR / f"{recipe_name}.txt"
    subprocess.run(["cat", recipe_path])


def del_recipe(recipe_name: str) -> None:
    recipe_path = DIR / f"{recipe_name}.txt"
    if not recipe_path.exists():
        print(f"No recipe file found for '{recipe_name}'")
        return
    confirm = input(f"Are you sure you want to delete '{recipe_name}'? Y/n ")
    if confirm != "Y":
        Path.unlink(recipe_path)


def list_recipes():
    print("--- Recipes ---\n")
    for filename in sorted(DIR.iterdir()):
        if filename.is_file():
            print(f"* {filename.stem}")
    sys.exit(0)


def main():
    init()
    parser = argparse.ArgumentParser(prog="Linux Recipes")

    parser.add_argument("recipe", help="Name of the recipe to add, edit, view or delete.")
    parser.add_argument(
        "-v", "--view", action="store_true", help="View the recpie file i the console."
    )
    parser.add_argument(
        "-n", "--new", action="store_true", help="Create new recipe file. Add -e flag to edit."
    )
    parser.add_argument(
        "-d", "--delete", action="store_true", help="Delete specified recipe with confirmation prompt."
    )
    parser.add_argument(
        "-e", "--edit", action="store_true", help="Open file in specified editor (defaults to vim)"
    )
    
    args = parser.parse_args()

    if args.recipe == "list":
        list_recipes()

    if args.view:
        view_recipe(args.recipe)
    if args.new:
        make_recipe(args.recipe)
    if args.edit:
        edit_recipe(args.recipe)
    if args.delete:
        del_recipe(args.recipe)
    # If blocks to catch operation


if __name__ == "__main__":
    main()
