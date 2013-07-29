from flexmock import flexmock
from framework.db.db import DB
from framework.random import Random


class DBEnvironmentBuilder():

    def build(self):
        self._create_core_mock()
        db = flexmock(DB(self.core_mock))
        db.should_receive("InitDB")  # Neutralize the access to the file system
        db.GetDBNames_old = db.GetDBNames
        db.should_receive("GetDBNames").and_return(["db1", "db2", "HTMLID_DB"])
        db.Storage['SEED_DB'] = {"seed/path": {'Data': [], 'SyncCount': 0}}
        return db

    def _create_core_mock(self):
        self.core_mock = flexmock()
        self.core_mock.Random = Random()
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("GetAll").and_return(["path"])

        def fake_get(key):  #  Faster than loading the real config object
            values = {"REGEXP_FILE_URL": "^[^\?]+\.(xml|exe|pdf|cs|log|inc|dat|bak|conf|cnf|old|zip|7z|rar|tar|gz|bz2|txt|xls|xlsx|doc|docx|ppt|pptx)$",
                      "REGEXP_SMALL_FILE_URL": "^[^\?]+\.(xml|cs|inc|dat|bak|conf|cnf|old|txt)$",
                      "REGEXP_IMAGE_URL": "^[^\?]+\.(jpg|jpeg|png|gif|bmp)$",
                      "REGEXP_VALID_URL": "^(http|ftp)[^ ]+$",
                      "SIMULATION": True,
                      "SEED_DB": "seed/path",
                      "HTMLID_DB": "path"}
            return values[key]
        self.core_mock.Config.Get = fake_get