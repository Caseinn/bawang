import subprocess

from bawang import config


def play(url: str, title: str) -> int:
    args = ["mpv", url, f"--title={title}"]
    args.extend(config.MPV_DEFAULT_ARGS)
    args.extend(config.MPV_EXTRA_ARGS)
    completed = subprocess.run(args, check=False)
    return completed.returncode
