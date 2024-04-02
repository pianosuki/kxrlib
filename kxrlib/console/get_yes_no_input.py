from typing import Literal


def get_yes_no_input(prompt: str, default: Literal["y", "n"] = "y") -> bool:
    while True:
        prompt_with_default = prompt + (" [Y/n]: " if default.lower() == 'y' else " [y/N]: ")

        user_input = input(prompt_with_default).strip().lower()

        if not user_input:
            user_input = default

        if user_input in ["y", "yes"]:
            return True
        elif user_input in ["n", "no"]:
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
