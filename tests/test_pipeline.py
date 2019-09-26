import unittest
from .pipeline_integration import PipelineIntegrationTestCase

"""
ULL PIPELINE INTEGRATION TESTS

In order to create additional test one should complete the following steps:

1. Create proper JSON configuration script having: 
    - corpus related parameters refer to %ROOT/data;
    - Grammar Tester/Text Parser dictionary related variables refer to %ROOT/dict;
    - Dash board setup to have tested values in summary table saved as %CONFIG-summary.txt.
2. Run pipeline manually with previously created configuration file to make sure it works properly and have tested 
    values in dash board summary text file;
3. Rename dash board summary text file as follows: <test-name>-expected.txt to be used as reference when testing;
3. Make subdirectory in pipeline integration test directory (tests/test-data/pipeline) having the followind structure:
    <test-name>
        <test-name>.json
        <test-file>.expected
4. Create one more class method down in this file as follows:
    def test_<test-name>(self):
        self.run_pipeline_test_case("<test-name>", "<corpus-path>")
        
All <test-name> should be replaced with your test name. <corpus-path> should be replaced with path to either corpus file
or corpus directory relative to 'language-learning' project directory. 
Use already existing tests in (tests/test-data/pipeline) as examples when creating JSON configuration file and test
subdirectory structure.         

"""


class PipelineTestCase(PipelineIntegrationTestCase):

    # @unittest.skip
    def test_gl_gt(self):
        """ GL+GT ALE50 test case performed on CDS-clean corpus """
        self.run_pipeline_test_case("GL-GT-ALE", "data/CDS/LG-E-clean")

    # @unittest.skip
    def test_gl_djct_costs_CDS(self):
        """ GL(disjunct-cost)+GT ALE50 test case performed on CDS-clean corpus """
        self.run_pipeline_test_case("GL-DJCT-COSTS-CDS", "data/CDS/LG-E-clean")

    # @unittest.skip
    def test_pe(self):
        """ PE test case performed on POC-English-ref and POC-English-ref-multi parses """
        self.run_pipeline_test_case("PE",
                                    [
                                        ("tests/test-data/parses/poc-english-ref/poc_english.txt.ull", "single"),
                                        ("tests/test-data/parses/poc-english-multi-ref", "multi")
                                    ])

    # @unittest.skip
    def test_tp(self):
        """ TP test case performed on CDS-clean corpus (parses) """
        self.run_pipeline_test_case("TP", "data/CDS/LG-E-clean")

    # @unittest.skip
    def test_tp_text_corpus(self):
        """ TP test case performed on CDS-clean corpus (text) """
        self.run_pipeline_test_case("TP-TXT-CORPUS",
                                    [
                                        ("data/CDS/LG-E-clean", "ref")
                                    ])


if __name__ == '__main__':
    unittest.main()
