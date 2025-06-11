import zipfile
from pathlib import Path
from undetected_chromedriver.patcher import Patcher
from urllib.request import urlopen, urlretrieve
import sys
import json
from typing import Any

chrome_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"


def suppress_exception_in_del(uc: Any):
    """It suppresses an exception in uc's __del__ method, which is raised when
    selenium shuts down."""
    old_del = uc.Chrome.__del__

    def new_del(self: Any) -> None:
        try:
            old_del(self)
        except:
            pass

    setattr(uc.Chrome, '__del__', new_del)

def get_platform():
    platform = sys.platform
    if platform.endswith("win32"):
        # TODO: additional check needed to choose correct version
        return 'win64'          # or 'win32'
    if platform.endswith(("linux", "linux2")):
        return 'linux64'
    if platform.endswith("darwin"):
        # TODO: additional check needed to choose correct version
        return 'mac-x64'        # or 'mac-arm64'
    raise NotImplementedError("Unsupported platform: " + platform)


class UrlNotFound(Exception):
    pass


def get_chromedriver_fp():
    patcher = Patcher()
    driver_fp = Path(patcher.executable_path)
    driver_fp.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    driver_ver_fp = driver_fp.with_suffix('.ver')

    with urlopen(chrome_url) as f:
        data = json.loads(f.read().decode('utf-8'))
    stable_ch = data['channels']['Stable']
    latest_ver = stable_ch['version']

    cur_ver = None
    if driver_fp.exists() and driver_ver_fp.exists():
        cur_ver = driver_ver_fp.read_text(encoding='utf-8')
        if cur_ver == latest_ver:
            return str(driver_fp)       # doesn't need updating

    platforms = stable_ch['downloads']['chromedriver']
    this_platform = get_platform()
    url = None
    for p in platforms:
        if p['platform'] == this_platform:
            url = p['url']
    if url is None:
        raise UrlNotFound(f"url not found for platform `{this_platform}`")

    with zipfile.ZipFile(urlretrieve(url)[0]) as zf:
        for fp in zf.filelist:
            if Path(fp.filename).name.startswith('chromedriver'):
                driver_fp.unlink(missing_ok=True)
                driver_fp.write_bytes(zf.read(fp.filename))
                driver_fp.chmod(0o755)
                driver_ver_fp.write_text(latest_ver, encoding='utf-8')
                driver_ver_fp.chmod(0o755)
                return str(driver_fp)
    raise FileNotFoundError("chromedriver not found in zip file")
