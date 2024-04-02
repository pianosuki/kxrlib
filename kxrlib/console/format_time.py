def format_time(time: float) -> str:
    hours = int(time / 3600)
    minutes = int(time / 60) % 60
    seconds = int(time) % 60
    milliseconds = int(time * 1000) % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
