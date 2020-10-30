import typing
import os
import io

from PyQt5.QtCore import QUrl

import pytest

from qutebrowser.components.utils import blockutils

@pytest.fixture
def pretend_blocklists(tmpdir):
    """Put fake blocklists into a tempdir.

    Put fake blocklists blocklists into a temporary directory, then return
    both a list containing `file://` urls, and the residing dir.
    """
    data = [
        (["cdn.malwarecorp.is", "evil-industries.com"], "malicious-hosts.txt"),
        (["news.moms-against-icecream.net"], "blocklist.list"),
    ]
    # Add a bunch of automatically generated blocklist as well
    for n in range(8):
        data.append(([f"example{n}.com", f"example{n+1}.net"], f"blocklist{n}"))

    bl_dst_dir = tmpdir / "blocklists"
    bl_dst_dir.mkdir()
    urls = []
    for blocklist_lines, filename in data:
        bl_dst_path = bl_dst_dir / filename
        with open(bl_dst_path, "w", encoding="utf-8") as f:
            f.write("\n".join(blocklist_lines))
        assert os.path.isfile(bl_dst_path)
        urls.append(QUrl.fromLocalFile(str(bl_dst_path)).toString())
    return urls, bl_dst_dir


def test_blocklist_dl(pretend_blocklists):
    num_single = 0

    def on_single_download(download: typing.IO[bytes]) -> None:
        nonlocal num_single
        num_single += 1
        num_lines = 0
        for line in io.TextIOWrapper(download, encoding="utf-8"):
            assert line.split(".")[-1].strip() in ("com", "net", "is")
            num_lines += 1
        assert num_lines >= 1

    def on_all_downloaded(done_count: int) -> None:
        assert done_count == 10

    list_qurls = [QUrl(l) for l in pretend_blocklists[0]]

    dl = blockutils.BlocklistDownloads(list_qurls, on_single_download, on_all_downloaded)
    dl.initiate()
    while dl._in_progress:
        pass

    assert num_single == 10