import subprocess


def play(url: str, title: str) -> int:
    args = ["ffplay", "-autoexit", "-loglevel", "warning", url]
    completed = subprocess.run(args, check=False)
    return completed.returncode
