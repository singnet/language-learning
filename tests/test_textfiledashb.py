import unittest
import os

from grammar_test.textfiledashb import TextFileDashboard, DashboardError


class TextFileDashTestCase(unittest.TestCase):

    def test_init(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")

        self.assertTrue(hasattr(dboard, "_path"))
        self.assertTrue(hasattr(dboard, "_row_count"))
        self.assertTrue(hasattr(dboard, "_col_count"))
        self.assertTrue(hasattr(dboard, "_dashboard"))
        self.assertEqual(2, len(dboard._dashboard))

        for row in dboard._dashboard:
            self.assertEqual(2, len(row))

    def test_set_cell_by_indexes(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")
        dboard.set_cell_by_indexes(0, 0, "00")
        dboard.set_cell_by_indexes(0, 1, "01")
        dboard.set_cell_by_indexes(1, 0, "10")
        dboard.set_cell_by_indexes(1, 1, "11")

        with self.assertRaises(IndexError) as ctx:
            dboard.set_cell_by_indexes(4, 5, "45")

        self.assertEqual("list index out of range", str(ctx.exception))

    def test_set_row_names(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")
        dboard.set_row_names(["1", "2"])
        self.assertTrue(hasattr(dboard, "_row_names"))
        self.assertEqual(2, len(dboard._row_names))

    def test_set_row_names_exception(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")

        with self.assertRaises(ValueError) as ctx:
            dboard.set_row_names(["1", "2", "3"])

        self.assertEqual("'names' list size does not match the number of rows allocated", str(ctx.exception))

    def test_set_col_names(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")
        dboard.set_col_names(["A", "B"])
        self.assertTrue(hasattr(dboard, "_col_names"))
        self.assertEqual(2, len(dboard._col_names))

    def test_set_col_names_exception(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")

        with self.assertRaises(ValueError) as ctx:
            dboard.set_col_names(["A", "B", "C"])

        self.assertEqual("'names' list size does not match the number of columns allocated", str(ctx.exception))

    def test_get_row_index_not_set_exception(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")

        with self.assertRaises(DashboardError) as ctx:
            index = dboard._get_row_index("1")

        self.assertEqual("row names are not set", str(ctx.exception))

    def test_get_row_index(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")
        dboard.set_row_names(["1", "2"])
        self.assertEqual(0, dboard._get_row_index("1"))
        self.assertEqual(1, dboard._get_row_index("2"))

    def test_get_col_index_not_set_exception(self):
        dboard = TextFileDashboard(2, 2, "dashboard.txt")

        with self.assertRaises(DashboardError) as ctx:
            index = dboard._get_col_index("A")

        self.assertEqual("column names are not set", str(ctx.exception))

    def test_get_col_index(self):
        dboard = TextFileDashboard(2, 2, "test-data/temp/dashboard.txt")
        dboard.set_col_names(["A", "B"])
        self.assertEqual(0, dboard._get_col_index("A"))
        self.assertEqual(1, dboard._get_col_index("B"))

    def test_update_dashboard(self):
        file_path = "test-data/temp/dashboard.txt"

        try:
            os.unlink(file_path)
        except:
            pass

        dboard = TextFileDashboard(2, 2, file_path)
        dboard.set_col_names(["A", "B"])
        dboard.set_cell_by_indexes(0, 0, "00")
        dboard.set_cell_by_indexes(0, 1, "01")
        dboard.set_cell_by_indexes(1, 0, "10")
        dboard.set_cell_by_indexes(1, 1, "11")
        dboard.update_dashboard()

        self.assertTrue(os.path.isfile(file_path))


if __name__ == '__main__':
    unittest.main()
