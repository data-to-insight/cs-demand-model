from pathlib import Path

from fs.opener import Opener
from fs.osfs import OSFS


class SampleFSOpener(Opener):
    protocols = ["sample"]

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        import csdmpy_fakedata

        path = Path(csdmpy_fakedata.__file__).parent.resolve(strict=True)
        return OSFS(str(path / parse_result.resource))
