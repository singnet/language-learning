import unittest
from .pipeline_integration import ScriptIntegrationTestCase

"""
CLI SCRIPT INTEGRATION TESTS

In order to create additional test one should complete the following steps:

"""

# Root path for all CLI-scripts integration tests
TESTS_ROOT = "tests/test-data/cli-scripts"


class CLIScriptsTestCase(ScriptIntegrationTestCase):

    # @unittest.skip
    def test_parse_evaluator_ord_eval_mode(self):
        """ 'parse-evaluator' standard evaluation mode integration test performed on POC-English corpus """
        corpus_path = "tests/test-data/parses/poc-english-ref/poc_english.txt.ull"
        tmpdir_path = self.prepare_test(f"{TESTS_ROOT}/parse-evaluator/ord-eval-mode", corpus_path)
        output_file = f"{tmpdir_path}/output.txt"

        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} --verbosity=debug",
                        output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_ord_multi(self):
        """ 'parse-evaluator' evaluation mode integration test performed on multi-file POC-English corpus """
        corpus_path = "tests/test-data/parses/poc-english-multi-ref"
        tmpdir_path = self.prepare_test(f"{TESTS_ROOT}/parse-evaluator/ord-eval-multi", corpus_path)
        output_file = f"{tmpdir_path}/output.txt"

        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} --verbosity=debug",
                        output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_ord_seq_mode(self):
        """ 'parse-evaluator' sequential mode integration test performed on POC-English corpus """
        corpus_path = "tests/test-data/parses/poc-english-ref/poc_english.txt.ull"
        tmpdir_path = self.prepare_test(f"{TESTS_ROOT}/parse-evaluator/ord-seq-mode", corpus_path)
        output_file = f"{tmpdir_path}/ord-output.txt"

        # Run script in ordinary mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} -s -i", output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_alt_seq_mode(self):
        """ 'parse-evaluator' alternative sequential mode integration test performed on POC-English corpus """
        corpus_path = "tests/test-data/parses/poc-english-ref/poc_english.txt.ull"
        tmpdir_path = self.prepare_test(f"{TESTS_ROOT}/parse-evaluator/alt-seq-mode", corpus_path)
        output_file = f"{tmpdir_path}/alt-output.txt"

        # Run script in alternative mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} -s -i -a", output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_alt_flt_mode(self):
        """ 'parse-evaluator' alternative filtering mode integration test performed on subset of GCB corpus """
        config_path = f"{TESTS_ROOT}/parse-evaluator/alt-flt-mode"
        corpus_path = f"{config_path}/1332-0.txt.ull"

        # Create temporary test directory filled with all necessary for the test to be executed
        tmpdir_path = self.prepare_test(config_path, corpus_path)
        output_file = f"{tmpdir_path}/alt-output.txt"

        # Run script in alternative mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} -f -i -a", output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_ord_flt_mode(self):
        """ 'parse-evaluator' filtering mode integration test performed on subset of GCB corpus """
        config_path = f"{TESTS_ROOT}/parse-evaluator/ord-flt-mode"
        corpus_path = f"{config_path}/1332-0.txt.ull"

        # Create temporary test directory filled with all necessary for the test to be executed
        tmpdir_path = self.prepare_test(config_path, corpus_path)
        output_file = f"{tmpdir_path}/ord-output.txt"

        # Run script in ordinary mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} -f -i", output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_alt_tok_mode(self):
        """ 'parse-evaluator' alternative filtering mode integration test performed on subset of GCB corpus """
        config_path = f"{TESTS_ROOT}/parse-evaluator/alt-tok-mode"
        corpus_path = f"{config_path}/sentence-2.txt.ull"
        refern_path = f"{config_path}/sentence-1.txt.ull"

        # Create temporary test directory filled with all necessary for the test to be executed
        tmpdir_path = self.prepare_test(config_path)
        output_file = f"{tmpdir_path}/alt-output.txt"

        # Run script in alternative mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {refern_path} -O {tmpdir_path} -o -i -a", output_file)

        self.check_expectations(tmpdir_path)

    # @unittest.skip
    def test_parse_evaluator_ord_tok_mode(self):
        """ 'parse-evaluator' ordinary filtering mode integration test performed on subset of GCB corpus """
        config_path = f"{TESTS_ROOT}/parse-evaluator/ord-tok-mode"
        corpus_path = f"{config_path}/sentence-2.txt.ull"
        refern_path = f"{config_path}/sentence-1.txt.ull"

        # Create temporary test directory filled with all necessary for the test to be executed
        tmpdir_path = self.prepare_test(config_path)
        output_file = f"{tmpdir_path}/ord-output.txt"

        # Run script in alternative mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {refern_path} -O {tmpdir_path} -o -i", output_file)

        self.check_expectations(tmpdir_path)

    @unittest.skip
    def test_parse_evaluator_ord_rnd_single(self):
        """ 'parse-evaluator' random mode integration test performed on POC-English corpus """
        corpus_path = "tests/test-data/parses/poc-english-ref/poc_english.txt.ull"
        tmpdir_path = self.prepare_test(f"{TESTS_ROOT}/parse-evaluator/ord-rnd-single", corpus_path)
        output_file = f"{tmpdir_path}/ord-output.txt"

        # Run script in ordinary mode
        self.run_script(f"parse-evaluator -t {corpus_path} -r {corpus_path} -O {tmpdir_path} -z -i", output_file)

        self.check_expectations(tmpdir_path)


if __name__ == '__main__':
    unittest.main()
