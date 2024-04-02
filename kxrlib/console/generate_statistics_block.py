from collections import deque


def generate_statistics_block(
        title: str,
        desc_strings: list[str],
        value_strings: list[str],
        block_top_bottom_char: str = "=",
        block_left_right_char: str = "|",
        separator_char: str = ":"
) -> str:
    if not isinstance(desc_strings, list):
        raise TypeError(f"Argument 'desc_strings' must be {list}, not {type(desc_strings)}")
    if not isinstance(value_strings, list):
        raise TypeError(f"Argument 'value_strings' must be {list}, not {type(value_strings)}")
    if not len(desc_strings) == len(value_strings):
        raise ValueError(f"Arguments 'desc_strings' (length={len(desc_strings)}) and 'value_strings' (length={len(value_strings)}) must contain the same number of items")

    statistics_dict = dict(zip(desc_strings, value_strings))

    max_desc_length = max(len(desc) for desc in desc_strings)
    max_value_length = len(max(value_strings, key=len))

    title_is_odd = len(title) % 2 != 0
    max_desc_is_odd = max_desc_length % 2 != 0
    max_value_is_odd = max_value_length % 2 != 0

    add_extra_char = (
        (title_is_odd and max_desc_is_odd and not max_value_is_odd) or
        (title_is_odd and not max_desc_is_odd and max_value_is_odd) or
        (not title_is_odd and not max_desc_is_odd and not max_value_is_odd) or
        (not title_is_odd and max_desc_is_odd and max_value_is_odd)
    )

    top_spacer_size = (
        (max_desc_length + max_value_length + 7 - len(title) - 2) // 2
        + (1 if add_extra_char else 0)
    )

    bottom_spacer_size = (
        max_desc_length + max_value_length + 7
        + (1 if add_extra_char else 0)
    )

    summary_strings = deque([
        f"{block_left_right_char} "
        f"{desc} "
        f"{' ' * (max_desc_length - len(desc))}"
        f"{separator_char} "
        f"{value} "
        f"{' ' * (max_value_length - len(value))}"
        f"{' ' if add_extra_char else ''}"
        f"{block_left_right_char}\n"
        for desc, value in statistics_dict.items()
    ])

    summary_strings.appendleft(f"{block_top_bottom_char * top_spacer_size} {title} {block_top_bottom_char * top_spacer_size}\n")
    summary_strings.append(f"{block_top_bottom_char * bottom_spacer_size}")

    return "".join(summary_strings)
