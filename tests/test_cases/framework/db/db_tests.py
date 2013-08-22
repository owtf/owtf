from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from tests.testing_framework.db.environments import DBEnvironmentBuilder
import unittest


class DBTests(BaseTestCase):

    def before(self):
        try:
            environment_builder = DBEnvironmentBuilder()
            self.db = environment_builder.build()
            self.core_mock = environment_builder.core_mock
            self.db.Init()
        except Exception, e:
            print "Exception!"

    def test_Init_initializes_the_DBs(self):
        assert_that("db1" in self.db.DBHandler.Storage)
        assert_that("db2" in self.db.DBHandler.Storage)
        assert_that("HTMLID_DB" in self.db.DBHandler.Storage)

    @unittest.skip("Implementation changed")
    def test_Search_by_criteria(self):
        name_to_offset = {"field": 0}
        criteria = {"field": "value"}
        self.db.Add("db1", ["value"], "path")
        self.db.should_receive("GetPath").and_return("path")

        results = self.db.Search("db1", criteria, name_to_offset)

        assert_that(results is not None)
        assert_that(results, has_length(greater_than(0)))

    @unittest.skip("Implementation changed")
    def test_GetNextHTMLID_generates_a_new_ID(self):
        first_id = self.db.GetNextHTMLID()
        second_id = self.db.GetNextHTMLID()

        assert_that(first_id, is_not(equal_to(second_id)))

    @unittest.skip("Implementation changed")
    def test_GetDBNames_delegates_on_the_config_obj_and_returns_a_list(self):
        db_names_length = times = len(self.db.DBHandler.DBNames)
        self.core_mock.Config.should_receive("Get").and_return("db_name").times(times)

        result = self.db.DBHandler.GetDBNames_old()  # Backup of the method, replaced in the initialization

        assert_that(result, has_length(equal_to(db_names_length)))
