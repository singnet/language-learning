import os
import sys
import shutil
import datetime
import unittest
from subprocess import PIPE, Popen
# from __future__ import __annotations__
from typing import Union, Tuple, List, Optional, Type
from src.common.dirhelper import traverse_dir_tree
# from src.common.absclient import AbstractFileParserClient


# Root path where all LG dictionary subdirectories are located
DICT_REL_PATH = "tests/test-data/dict"


class PipelineIntegrationBaseTestCase(unittest.TestCase):
    """
    Pipeline integration test base class

    """
    @staticmethod
    def run_pipeline(config_path: str) -> int:
        """
        Run pipeline defined by JSON configuration file

        :param config_path:     JSON configuration file.
        :return:                OS error level
        """
        ull_cli = shutil.which("ull-cli")

        if ull_cli is None:
            raise FileNotFoundError("'ull-cli' is not found.")

        with Popen([ull_cli, "-C", config_path, "--logging=debug"], stdout=PIPE) as proc:
            proc.communicate()

            ret_code = proc.returncode

        return ret_code

    @staticmethod
    def run_script(cmd_line: str, output_path: Optional[str]):
        """
        Run CLI script

        :param cmd_line:        Command line including name of the script and all arguments.
        :param output_path:     File path to save 'stdout' output to.
        :return:                OS error level.
        """
        arg_list = cmd_line.split()

        cmd = shutil.which(arg_list[0])

        if cmd is None:
            raise FileNotFoundError(f"'{cmd}' is not found.")

        with Popen([cmd, *arg_list[1:]], stdout=PIPE) as proc:
            raw, err = proc.communicate()

            if output_path is not None:
                with open(output_path, "w") as out_file:
                    out_file.write(raw.decode("utf-8-sig"))

            ret_code = proc.returncode

        return ret_code

    @staticmethod
    def _compare_text_files(test_path: str, ref_path: str) -> bool:
        """
        Compare pipeline dash board summaries

        :param test_path:       Path to summary file, produced during pipeline test run.
        :param ref_path:        Path to reference summary file
        :return:                True if summaries are identical, False otherwise.
        """
        with open(test_path, "r") as test_file:
            test_lines = test_file.readlines()

        with open(ref_path, "r") as ref_file:
            ref_lines = ref_file.readlines()

        if len(test_lines) != len(ref_lines):
            return False

        for t, r in zip(test_lines, ref_lines):
            t_tokens = t.split()
            r_tokens = r.split()

            if len(t_tokens) != len(r_tokens):
                return False

            for tt, rr in zip(t_tokens, r_tokens):
                if tt.strip() != rr.strip():
                    return False

        return True

    @staticmethod
    def _print_text_file(path: str) -> None:
        """
        Print text file (text dash board) to stderr

        :param path:        Path to the file.
        :return:            None
        """
        with open(path, "r") as file:
            text = file.read()
            print(f"\n{path}:\n{text}", file=sys.stderr)

    @staticmethod
    def compare_text_files(test_path: str, ref_path: str):
        """
        Compare pipeline dash board summaries and print out both files in case of any differences.

        :param test_path:       Path to summary file, produced during pipeline test run.
        :param ref_path:        Path to reference summary file
        :return:                True if summaries are identical, False otherwise.
        """
        if not PipelineIntegrationTestCase._compare_text_files(test_path, ref_path):
            PipelineIntegrationTestCase._print_text_file(test_path)
            PipelineIntegrationTestCase._print_text_file(ref_path)
            return False

        return True

    @staticmethod
    def create_sym_link(data_path: str, root: str, name: str = "data"):
        """
        Create symbolic link for given file or directory

        :param data_path:       Path to a file or directory.
        :param root:            Root path where symbolic link is to be created.
        :param name:            Name of the symbolic link to be created.
        :return:
        """
        pwd = os.environ["PWD"]

        if os.path.isfile(data_path):
            os.mkdir(f"{root}/{name}")
            os.symlink(f"{pwd}/{data_path}", f"{root}/{name}/{os.path.split(data_path)[1]}")

        elif os.path.isdir(data_path):
            os.symlink(f"{pwd}/{data_path}", f"{root}/{name}", True)

        else:
            raise FileNotFoundError("Corpus file/directory does not exist.")

    @staticmethod
    def prepare_test(test_path: str, data_path: Union[str, List[Tuple[str, str]], None] = None) -> str:
        """
        Prepare pipeline test temporary directory:
            - create temporary directory;
            - copy all files from 'test_path' to the temporary directory;
            - create symbol link to a corpus file/directory

        :param test_path:       Path to a directory where test files reside.
        :param data_path:       Path to a corpus file or directory/List of tuples (path, link_name).
        :return:                Path to prepared test directory
        """
        if not os.path.isdir(test_path):
            raise FileNotFoundError(f"'{test_path}' does not exist.")

        if test_path.endswith("/"):
            test_path = test_path[:-1]

        last_slash_pos = test_path.rfind("/")
        test_dir_name = test_path if last_slash_pos < 0 else test_path[last_slash_pos+1:]
        path_to_create = "/var/tmp/" + test_dir_name

        # Remove temporary directory if it's already there
        if os.path.isdir(path_to_create):
            shutil.rmtree(path_to_create)

        # Copy directory pointed by 'test_path' to a new temporary directory
        shutil.copytree(test_path, path_to_create)

        pwd = os.environ["PWD"]

        if isinstance(data_path, str):
            PipelineIntegrationTestCase.create_sym_link(data_path, path_to_create)

        elif isinstance(data_path, list):
            for entry in data_path:
                PipelineIntegrationTestCase.create_sym_link(entry[0], path_to_create, entry[1])

        # Create 'dict' pseudo directory
        os.symlink(f"{pwd}/{DICT_REL_PATH}", path_to_create + f"/dict", True)

        return path_to_create

    @staticmethod
    def compare_dict_files(tst_dict_path: str, ref_dict_path: str) -> bool:
        """
        Compare .dict files line by line leaving out comments.

        :param tst_dict_path:   Test dictionary file path.
        :param ref_dict_path:   Reference dictionary file path.
        :return:                True if all lines match, Fales otherwise.
        """
        with open(tst_dict_path, "r") as tst_handle, open(ref_dict_path, "r") as ref_handle:
            test_lines = tst_handle.readlines()
            ref_lines = ref_handle.readlines()

        if len(test_lines) != len(ref_lines):
            return False

        for t, r in zip(test_lines, ref_lines):
            t, r = t.strip(), r.strip()

            if len(t) and t[0] == "%":
                continue

            if t.strip() != r.strip():
                return False

        return True

    @staticmethod
    def _compare_stat_files(tst_stat_path: str, ref_stat_path: str) -> bool:
        """
        Compare .stat files ignoring "Parse time"

        :param tst_stat_path:   Test statistics file path.
        :param ref_stat_path:   Reference statistics file path.
        :return:                True if all "comparable" fields match.
        """
        with open(tst_stat_path, "r") as tst_handle, open(ref_stat_path, "r") as ref_handle:
            test_lines = tst_handle.readlines()
            ref_lines = ref_handle.readlines()

        if len(test_lines) != len(ref_lines):
            return False

        for t, r in zip(test_lines, ref_lines):
            t, r = t.strip(), r.strip()

            if len(t) < 1 or t.startswith("Parse time"):
                continue

            t_param, r_param = t.split(":"), r.split(":")

            if len(t_param) != 2 or len(r_param) != 2:
                return False

            t_name, r_name = t_param[0].strip(), r_param[0].strip()

            if t_name != r_name or t_param[1].strip() != r_param[1].strip():
                return False

        return True

    @staticmethod
    def compare_stat_files(tst_stat_path: str, ref_stat_path: str) -> bool:
        """
        Compare .stat files ignoring "Parse time"

        :param tst_stat_path:   Test statistics file path.
        :param ref_stat_path:   Reference statistics file path.
        :return:                True if all "comparable" fields match.
        """
        if not PipelineIntegrationTestCase._compare_stat_files(tst_stat_path, ref_stat_path):
            PipelineIntegrationTestCase._print_text_file(tst_stat_path)
            PipelineIntegrationTestCase._print_text_file(ref_stat_path)
            return False

        return True

    def check_expectations(self, tmp_test_path: str):
        """
        Compare all files ending with ".expected" suffix with their respective counterparts

        :param tmp_test_path:   Path to test directory
        :return:                None
        """
        def on_file(ref_path: str, args: List[str]) -> None:
            """
            Comparison callback function

            :param ref_path:    Reference file path.
            :param args:        Extra arguments, if any.
            :return:            None.
            """
            # Get test file name by trimming of '.expected' suffix
            test_path = f"{ref_path[:-9]}"

            # Check if there is a summary file in the directory
            self.assertTrue(os.path.isfile(test_path), f"File '{test_path}' is not found.")

            if test_path.endswith(".dict"):
                self.assertTrue(self.compare_dict_files(test_path, ref_path),
                                f"'{test_path}' and '{ref_path}' mismatch.")

            elif test_path.endswith(".stat"):
                self.assertTrue(self.compare_stat_files(test_path, ref_path),
                                f"'{test_path}' and '{ref_path}' mismatch.")
            else:
                # Compare summaries
                self.assertTrue(self.compare_text_files(ref_path, test_path),
                                f"'{test_path}' and '{ref_path}' mismatch.")

        traverse_dir_tree(tmp_test_path, ".expected", [on_file], None, True)

    @staticmethod
    def shift_dict_expectations(tmp_test_path: str):
        """
        Rename dictionary files to match the current date

        :param tmp_test_path:   Temporary test path.
        :return:                None.
        """
        def on_dict(dict_path: str, args: List[str]) -> None:
            # Split path into a path itself and file name
            file_path, file_name = os.path.split(dict_path)

            # Split file name into dictionary parameters
            splitted = file_name.split("_")

            # Replace date with the current date
            splitted[2] = datetime.datetime.utcnow().strftime("%Y-%m-%d")

            # Join parameters to make a new file path
            updated_path = os.path.join(file_path, f"{'_'.join(splitted)}")

            # Rename dictionary file with a newly made name
            os.rename(dict_path, updated_path)

        traverse_dir_tree(tmp_test_path, ".dict.expected", [on_dict], None, True)


class PipelineIntegrationTestCase(PipelineIntegrationBaseTestCase):
    """
    Pipeline integration test class

    """
    # Root path for all pipeline integration tests
    TESTS_ROOT = "tests/test-data/pipeline"

    def run_pipeline_test_case(self, test_name: str, data_path: Union[str, List[Tuple[str, str]]]) -> None:
        """
        Execute pipeline integration test

        :param test_name:       Test test/subdirectory name.
        :param data_path:       Path to a corpus file/directory.
        :return:                None
        """
        test_path = f"{self.TESTS_ROOT}/{test_name}"

        tmp_test_path = self.prepare_test(test_path, data_path)

        self.assertEqual(f"/var/tmp/{test_name}", tmp_test_path)
        self.assertTrue(os.path.isdir(tmp_test_path))

        # Rename '.dict.expected' files to match current date
        self.shift_dict_expectations(tmp_test_path)

        # Run pipeline
        self.assertEqual(0, self.run_pipeline(f"{tmp_test_path}/{test_name}.json"),
                         f"Error executing pipeline. See '{tmp_test_path}/{test_name}.log' for details.")

        # Compare all expected files with their respective test results
        self.check_expectations(tmp_test_path)

        # Remove temporary directory on success
        # shutil.rmtree(tmp_test_path)


class ScriptIntegrationTestCase(PipelineIntegrationBaseTestCase):
    """
    General CLI script integration test case

    """
    # Root path for all CLI-scripts integration tests
    TESTS_ROOT = "tests/test-data/cli-scripts"

    @staticmethod
    def run_script(cmd_line: str, output_path: Optional[str]):
        """
        Run CLI script

        :param cmd_line:        Command line including name of the script and all arguments.
        :param output_path:     File path to save 'stdout' output to.
        :return:                OS error level.
        """
        arg_list = cmd_line.split()

        cmd = shutil.which(arg_list[0])

        if cmd is None:
            raise FileNotFoundError(f"'{cmd}' is not found.")

        with Popen([cmd, *arg_list[1:]], stdout=PIPE) as proc:
            raw, err = proc.communicate()

            if output_path is not None:
                with open(output_path, "w") as out_file:
                    out_file.write(raw.decode("utf-8-sig"))

            ret_code = proc.returncode

        return ret_code
