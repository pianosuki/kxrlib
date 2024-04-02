from collections import deque


def generate_begin_end_blocks(title: str, width: int, block_char: str = "=") -> tuple[str, str]:
    if not isinstance(width, int):
        raise TypeError(f"Argument 'width' must be {int}, not {type(width)}")

    begin_title = f"BEGIN {title.upper()}"
    end_title = f"END {title.upper()}"

    begin_title_is_odd = len(begin_title) % 2 != 0
    end_title_is_odd = len(end_title) % 2 != 0
    width_is_odd = width % 2 != 0

    begin_add_extra_char = (
        (begin_title_is_odd and not width_is_odd) or
        (not begin_title_is_odd and width_is_odd)
    )

    end_add_extra_char = (
            (end_title_is_odd and not width_is_odd) or
            (not end_title_is_odd and width_is_odd)
    )

    begin_spacer_size = (width - len(begin_title) - 2) // 2
    end_spacer_size = (width - len(end_title) - 2) // 2

    begin_block_strings = deque([
        f"{block_char * begin_spacer_size} "
        f"{begin_title.upper()} "
        f"{block_char * begin_spacer_size}"
        f"{(block_char if begin_add_extra_char else '')}\n"
    ])

    begin_block_strings.appendleft(f"{block_char * width}\n")
    begin_block_strings.append(f"{block_char * width}")

    end_block_strings = deque([
        f"{block_char * end_spacer_size} "
        f"{end_title.upper()} "
        f"{block_char * end_spacer_size}"
        f"{(block_char if end_add_extra_char else '')}\n"
    ])

    end_block_strings.appendleft(f"{block_char * width}\n")
    end_block_strings.append(f"{block_char * width}")

    return "".join(begin_block_strings), "".join(end_block_strings)
