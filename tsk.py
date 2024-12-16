#!/bin/env python3

"""
PyOrg

Simple CLI utility to manage tasks. Useful if you spend your life in the command line.

"""

import sys
import argparse
import pickle
from pathlib import Path

USER = "kyle"
DATA_PATH = Path(f"/home/{USER}/.org/tasks.pkl")

class TaskManager:
    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = data_path
        self.tasks = self.load_tasks()

    def init(self):
        """Initialize the tasks file if it doesn't exist."""
        if not self.data_path.parent.exists():
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.data_path.exists():
            print(f"No data file found, creating new at '{self.data_path}'")
            self.save_tasks([])

    def load_tasks(self) -> list:
        """Load tasks from pickle file."""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'rb') as f:
                    return pickle.load(f)
            return []
        except (FileNotFoundError, pickle.UnpicklingError):
            return []

    def save_tasks(self, tasks: list):
        """Save tasks to pickle file."""
        with open(self.data_path, 'wb') as f:
            pickle.dump(tasks, f)

    def sort_tasks(self, tasks: list[dict] = None) -> list:
        """Sort tasks by priority (high to low)."""
        if tasks is None:
            tasks = self.tasks
        return sorted(tasks, key=lambda x: x['priority'], reverse=True)

    def add_task(self, title: str, priority: int):
        """Add a new task."""
        if priority not in (1, 2, 3):
            raise ValueError("Priority is 1 = LOW, 2 = MEDIUM, 3 = HIGH")
        
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "priority": priority
        }
        self.tasks.append(task)
        self.save_tasks(self.tasks)
        print(f"Task added: {task}")

    def del_task(self, task_id: int):
        """Delete a task by ID."""
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                deleted_task = self.tasks.pop(i)
                self.save_tasks(self.tasks)
                print(f"Deleted task: {deleted_task}")
                return
        print(f"No task found with ID {task_id}")

    def view_tasks(self):
        """View all tasks."""
        if not self.tasks:
            print("No tasks found.")
            return

        sorted_tasks = self.sort_tasks()
        print("Current Tasks:")
        for task in sorted_tasks:
            print(f"ID: {task['id']} | Priority: {task['priority']} | Title: {task['title']}")

    def clear_tasks(self):
        """Clear all tasks."""
        self.tasks = []
        self.save_tasks(self.tasks)
        print("All tasks cleared.")

def main():
    parser = argparse.ArgumentParser(description="PyOrg - Simple Task Management CLI")
    parser.add_argument('action', choices=['init', 'add', 'delete', 'view', 'clear'], 
                        help='Action to perform')
    parser.add_argument('-t', '--title', help='Task title')
    parser.add_argument('-p', '--priority', type=int, choices=[1,2,3], 
                        help='Task priority (1=LOW, 2=MEDIUM, 3=HIGH)')
    parser.add_argument('-i', '--id', type=int, help='Task ID for deletion')

    args = parser.parse_args()

    task_manager = TaskManager()

    try:
        if args.action == 'init':
            task_manager.init()
        elif args.action == 'add':
            if not args.title or not args.priority:
                parser.error("Add requires both --title and --priority")
            task_manager.add_task(args.title, args.priority)
        elif args.action == 'delete':
            if not args.id:
                parser.error("Delete requires --id")
            task_manager.del_task(args.id)
        elif args.action == 'view':
            task_manager.view_tasks()
        elif args.action == 'clear':
            task_manager.clear_tasks()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
