# !/usr/bin/env python3
'''Pre-cleaner unittests and complete module test.
Run test:
cd language-learning
python tests/test_precleaner.py
'''

import os, sys
import unittest
import filecmp

module_path = os.path.abspath(os.path.join('.'))
if module_path not in sys.path: sys.path.append(module_path)
from src.pre_cleaner.pre_cleaner import *

class PreCleanerTestCase(unittest.TestCase):

	def test_Remove_Long_Tokens(self):
		max_chars = 5
		token_list = ["a" * (max_chars - 1), "a" * max_chars, "a" * (max_chars + 1)]
		cleaned_list = ["a" * (max_chars - 1), "a" * max_chars]

		self.assertEqual(Remove_Long_Tokens(token_list, max_chars), cleaned_list)

	def test_Ignore_Long_Sentence(self):
		max_tokens = 5
		list_short = list(range(max_tokens - 1))
		list_exact = list(range(max_tokens))
		list_long = list(range(max_tokens + 1))

		self.assertTrue(not Ignore_Long_Sentence(list_short, max_tokens))
		self.assertTrue(not Ignore_Long_Sentence(list_exact, max_tokens))
		self.assertTrue(Ignore_Long_Sentence(list_long, max_tokens))

	def test_Normalize_Tokens(self):
		apostrophes = "` ’ ‘" # different types of apostrophes
		apostrophes_ref = "' ' '"
		self.assertEqual(Normalize_Sentence(apostrophes, False), apostrophes_ref)

		dashes = "‑ ‐" # different types of dashes
		dashes_ref = "- -"
		self.assertEqual(Normalize_Sentence(dashes, False), dashes_ref)

		long_dashes = "-- ---- ― — – ‒" # different types of long dashes
		long_dashes_ref = "— — — — — —"
		self.assertEqual(Normalize_Sentence(long_dashes, False), long_dashes_ref)

		double_quotes = "'' “ ”" # different types of double quotes
		double_quotes_ref = '" " "'
		self.assertEqual(Normalize_Sentence(double_quotes, False), double_quotes_ref)

		mixed = "“ ’ ‐ ‑‑ ``" # Assortment of the above
		mixed_ref = '" \' - — "'
		self.assertEqual(Normalize_Sentence(mixed, False), mixed_ref)

	def test_Forbidden_Symbols(self):
		invalid_chars = 'aeiou'
		sentence = "This is a normal sentence"
		sentence_ref = "Ths s  nrml sntnc"
		self.assertEqual(Clean_Sentence(sentence, invalid_chars, []), sentence_ref)

	def test_Boundary_Chars(self):
		boundary_chars = 'a e i o u'
		sentence = "This is unusual for a sentence"
		sentence_ref = "This  i s  u nusual for a sentenc e "
		self.assertEqual(Char_Tokenizer(sentence, boundary_chars, ""), sentence_ref)

		boundary_chars = "\" ' \."
		sentence2 = "We're testin' another. \"sentence\"."
		sentence2_ref = "We're testin '  another .   \" sentence \" ."
		self.assertEqual(Char_Tokenizer(sentence2, boundary_chars, ""), sentence2_ref)

	def test_Splitter_Symbols(self):
		sentence = "This_is a t*est sen—tence—."
		sentence_ref = "This is a t est sen tence ."
		self.assertEqual(Clean_Sentence(sentence, "", []), sentence_ref)

	def test_Tokenized_Chars(self):
		tokenized_chars = ".?!"
		sentence = "A.test! sentence?."
		sentence_ref = "A . test !  sentence ?  . "
		self.assertEqual(Char_Tokenizer(sentence, "", tokenized_chars), sentence_ref)

	def test_Remove_Invalid_Tokens(self):
		invalid_token_symbols = "a i"
		tok_list = ["This", "is", "a", "test", "sentence"]
		tok_list_ref = ["test", "sentence"]
		self.assertEqual(Remove_Invalid_Tokens(tok_list, invalid_token_symbols), tok_list_ref)

	def test_Symbol_Invalidate_Sentence(self):
		invalid_sent_symbols = "a $"
		tok_list = ["This", "is", "a", "test", "sentence"]
		tok_list2 = ["Shorter", "test", "sentence"]
		self.assertTrue(Ignore_Invalid_Sentence(tok_list, invalid_sent_symbols, []))
		self.assertTrue(not Ignore_Invalid_Sentence(tok_list2, invalid_sent_symbols, []))

	def test_Token_Invalidate_Sentence(self):
		invalid_sent_tokens = ["is", "evil"]
		tok_list = ["This", "is", "a", "test", "sentence"]
		tok_list2 = ["This", "is", "an", "evil", "test", "sentence"]
		tok_list3 = ["Innocent", "sentence"]
		self.assertTrue(Ignore_Invalid_Sentence(tok_list, "", invalid_sent_tokens))
		self.assertTrue(Ignore_Invalid_Sentence(tok_list2, "", invalid_sent_tokens))
		self.assertTrue(not Ignore_Invalid_Sentence(tok_list3, "", invalid_sent_tokens))

	def test_Substitute_Numbers(self):
		num_test1 = "Those 3 dogs ate -4.1 hot dogs 3'"
		num_test1_ref = "Those  @number@  dogs ate  @number@  hot dogs  @number@ '"
		self.assertEqual(Substitute_Numbers(num_test1), num_test1_ref)
		num_test2 = "Adding 0,000,000 to 17;311.13 is -useless; it's #1 nonesense"
		num_test2_ref = "Adding  @number@  to  @number@  is -useless; it's  @number@  nonesense"
		self.assertEqual(Substitute_Numbers(num_test2), num_test2_ref)
		num_test3 = "Notatio.n: -51,123123 and 884'432'211 are 3cky. Section 3.B"
		num_test3_ref = "Notatio.n:  @number@  and  @number@  are 3cky. Section 3.B"
		self.assertEqual(Substitute_Numbers(num_test3), num_test3_ref)

	def test_Substitute_Dates(self):
		date_test1 = "On 5/13, meaning 5/13/2018, also written as 2018/5/13."
		date_test1_ref = "On  @date@ , meaning  @date@ , also written as  @date@ ."
		self.assertEqual(Substitute_Dates(date_test1), date_test1_ref)
		date_test2 = "Can't write as 5/2018/13, but 18-5-13 or 13.5.18"
		date_test2_ref = "Can't write as 5/2018/13, but  @date@  or  @date@ "
		self.assertEqual(Substitute_Dates(date_test2), date_test2_ref)
		date_test3 = "Try May 2018, or May 2018, specifically May 13th, 2018."
		date_test3_ref = "Try  @date@ , or  @date@ , specifically  @date@ ."
		self.assertEqual(Substitute_Dates(date_test3), date_test3_ref)
		date_test4 = "It was May-05-2018. Or 2018-May-13, but not 2018-XXX-13"
		date_test4_ref = "It was  @date@ . Or  @date@ , but not 2018-XXX-13"
		self.assertEqual(Substitute_Dates(date_test4), date_test4_ref)

	def test_Substitute_Times(self):
		time_test1 = "It's 4 am, woke up at 3:54AM, or 3:54:18am exactly"
		time_test1_ref = "It's  @time@ , woke up at  @time@ , or  @time@  exactly"
		self.assertEqual(Substitute_Times(time_test1), time_test1_ref)
		time_test2 = "Tomorrow at 16:10CEST, not 34:10"
		time_test2_ref = "Tomorrow at  @time@ , not 34:10"
		self.assertEqual(Substitute_Times(time_test2), time_test2_ref)

	def test_Substitute_Links(self):
		link_test1 = "Send me an email to not_my-address@666.com.uk"
		link_test1_ref = "Send me an email to  @email@ "
		self.assertEqual(Substitute_Links(link_test1), link_test1_ref)
		link_test2 = "https://any>thing?goes^*(-.!@here.#fsd_&.com installs malware."
		link_test2_ref = " @url@  installs malware."
		self.assertEqual(Substitute_Links(link_test2), link_test2_ref)

	def test_Substitute_Percent(self):
		percent_test2 = "Any number works 43.1% or -17,199%, not 12 %"
		percent_test2_ref = "Any number works  @percent@  or  @percent@ , not 12 %"
		self.assertEqual(Substitute_Percent(percent_test2), percent_test2_ref)

	def test_Remove_Suffixes(self):
		suffixes = "'re g"
		suffix_test1 = "They're coming tonight"
		suffix_test1_ref = "They comin tonight"
		new_suffixes = Prepare_Suffix_List(suffixes)
		self.assertEqual(Remove_Suffixes(suffix_test1, new_suffixes), suffix_test1_ref)

	def test_Separate_Contractions(self):
		test_sent = "I've haven't they're it's isn't some other's friends'"
		test_sent_ref = "I 've have n't they 're it 's is n't some other 's friends'"
		self.assertEqual(Normalize_Sentence(test_sent, True), test_sent_ref)

	def test_Execute_Precleaner(self):
		filename = "pg9212.txt"
		raw_dirpath = "tests/test-data/pre-cleaner/split-books/"
		cleaned_dirpath = "tests/test-data/pre-cleaner/cleaned-books/"
		cleaned_filepath = cleaned_dirpath + filename
		expected_filepath = "tests/test-data/pre-cleaner/expected-books/" + filename
		# Execute pre-cleaner with default parameters
		Execute_Precleaner(raw_dirpath, cleaned_dirpath)

		self.assertTrue(filecmp.cmp(expected_filepath, cleaned_filepath))





if __name__ == '__main__':
	unittest.main()