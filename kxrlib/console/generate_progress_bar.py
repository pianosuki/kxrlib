def generate_progress_bar(progress: float | int, length: int = 30) -> str:
    if not isinstance(progress, float) and not isinstance(progress, int):
        raise TypeError(f"Argument 'progress' must be one of {(float, int)}, not {type(progress)}")
    if not isinstance(length, int):
        raise TypeError(f"Keyword argument 'length' must be {int}, not {type(length)}")

    completed_length = int(length * progress)
    remaining_length = length - completed_length

    return f"[{'=' * completed_length}{' ' * remaining_length}]"
