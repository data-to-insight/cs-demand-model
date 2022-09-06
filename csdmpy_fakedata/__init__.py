from pathlib import Path

from csdmpy.datastore.zip import ZipDataStore

V1 = ZipDataStore(Path(__file__).parent / "v1.zip")
