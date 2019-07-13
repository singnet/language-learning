import os
import shutil
import unittest
from src.dash_board.textdashboard import TextFileDashboard, TextFileDashboardComponent
from src.pipeline.pipelinetree import get_component

conf =   {
    "component": "dash-board",
    "type": "static",
    "instance-name": "stat",
    "parameters": {
        "board_type": "file",
        "file_path":  "/var/tmp/dash-board/AGI-2018.txt",
        "board_name": "AGI-2018",
        "row_count": 17,
        "col_count": 10,
        "col_headers": [
          [
            {"title": "Corpus"},
            {"title": "Parsing/MI counting"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"},
            {"title": "Disjuncts/DRK/Disjuncts"},
            {"title": "Disjuncts/ILE/Disjuncts"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"},
            {"title": "Disjuncts/DRK/Disjuncts"},
            {"title": "Disjuncts/ILE/Disjuncts"}
          ]
        ]
    }
  }


less_headers =   {
    "component": "dash-board",
    "type": "static",
    "instance-name": "stat",
    "parameters": {
        "board_type": "file",
        "file_path":  "/var/tmp/dash-board/AGI-2018.txt",
        "board_name": "AGI-2018",
        "row_count": 17,
        "col_count": 10,
        "col_headers": [
          [
            {"title": "Corpus"},
            {"title": "Parsing/MI counting"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"},
            {"title": "Disjuncts/DRK/Disjuncts"},
            {"title": "Disjuncts/ILE/Disjuncts"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"}
          ]
        ]
    }
  }

more_headers =   {
    "component": "dash-board",
    "type": "static",
    "instance-name": "stat",
    "parameters": {
        "board_type": "file",
        "file_path":  "/var/tmp/dash-board/AGI-2018.txt",
        "board_name": "AGI-2018",
        "row_count": 17,
        "col_count": 10,
        "col_headers": [
          [
            {"title": "Corpus"},
            {"title": "Parsing/MI counting"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"},
            {"title": "Disjuncts/DRK/Disjuncts"},
            {"title": "Disjuncts/ILE/Disjuncts"},
            {"title": "Connectors/DRK/Connectors"},
            {"title": "Connectors/DRK/Disjuncts"},
            {"title": "Disjuncts/DRK/Disjuncts"},
            {"title": "Disjuncts/ILE/Disjuncts"},
            {"title": "Extra 1"},
            {"title": "Extra 2"}
          ]
        ]
    }
  }


multi =   {
    "component": "dash-board",
    "type": "static",
    "instance-name": "stat",
    "parameters": {
        "board_type": "file",
        "file_path":  "/var/tmp/dash-board-multi/test-summary.txt",
        "board_name": "test-summary",
        "row_count": 2,
        "col_count": 3,
        "col_headers": [
          [
            {"title": "CORPUS"},
            {"title": "MWC1"},
            {"title": "MWC2"}
          ]
        ],
        "multi_access": True
    }
  }


class DashboardTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = "/var/tmp/dash-board"

        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

    def test_something(self):
        should_be = "A\tB\tC\tD\n" \
                    "First\tN/A\t2\t3\n" \
                    "Second\t2\tN/A\t6\n" \
                    "Third\t3\t6\tN/A\n" \
                    "Fourth\t4\t8\t12\n"

        board = TextFileDashboard({
            "board_type": "file",
            "file_path":  f"{self.tmp_dir}/board.txt",
            "board_name": "TestBoard",
            "row_count": 4,
            "col_count": 4,
            "col_headers": [
              [
                {"title": "A"},
                {"title": "B"},
                {"title": "C"},
                {"title": "D"},
              ]
            ]
        })

        board.set_cell_by_indexes(1, 0, "First")
        board.set_cell_by_indexes(2, 0, "Second")
        board.set_cell_by_indexes(3, 0, "Third")
        board.set_cell_by_indexes(4, 0, "Fourth")

        for row in range(1, 5):
            for col in range(1, 4):
                if row != col:
                    board.set_cell_by_indexes(row, col, row * col)

        board.update_dashboard()

        self.assertEqual(should_be, str(board))

    def test_component(self):
        board = get_component("dash-board", conf["parameters"])
        board.set(row="1+1", col="1+ 3", val="23")
        self.assertTrue(True, True)

    def test_less_headers(self):
        board = get_component("dash-board", less_headers["parameters"])
        self.assertTrue(True, True)

    def test_more_headers(self):
        board = get_component("dash-board", more_headers["parameters"])
        self.assertTrue(True, True)

    def test_multi_access(self):
        conf_path = "tests/test-data/dash-board-multi"
        dest_path = "/var/tmp/dash-board-multi"

        if os.path.isdir(dest_path):
            shutil.rmtree(dest_path)

        shutil.copytree(conf_path, dest_path)

        board = get_component("dash-board", multi["parameters"])
        board.set(row="1", col="2", val="0.9")
        del board

        board = get_component("dash-board", multi["parameters"])
        board.set(row="2", col="2", val="1.0")
        del board


if __name__ == '__main__':
    unittest.main()
