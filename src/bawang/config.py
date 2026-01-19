import os
import shlex


BASE_URL = os.getenv("BWN_BASE_URL", "https://v1.samehadaku.how")
SEARCH_PATH = "/?s={query}"
ADMIN_AJAX_PATH = "/wp-admin/admin-ajax.php"
DEFAULT_TIMEOUT = 20.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
PREFERRED_PLAYERS = ["mpv", "ffplay"]
PREFERRED_HOSTS = [
    "googlevideo.com",
    "blogger.com",
    "wibufile.com",
    "samehadaku",
    "mega.nz",
    "filedon",
]
MPV_DEFAULT_ARGS = [
    "--cache=yes",
    "--cache-secs=20",
    "--demuxer-readahead-secs=20",
    "--demuxer-max-bytes=200M",
]
MPV_EXTRA_ARGS = shlex.split(os.getenv("BWN_MPV_ARGS", ""))
