#!/usr/bin/env python
# coding=utf-8
# runs on python3

# ASuMa, Feb 2018

import sys, getopt, os
import re
from html.parser import HTMLParser

__all__ = ['Execute_Precleaner', 'Ignore_Long_Sentence', 'Remove_Long_Tokens',
			'Normalize_Sentence', 'Clean_Sentence', 'Char_Tokenizer', 'Remove_Invalid_Tokens',
			'Ignore_Invalid_Sentence', 'Substitute_Numbers', 'Substitute_Dates',
			'Substitute_Times', 'Substitute_Links', 'Substitute_Percent',
			'Prepare_Suffix_List', 'Remove_Suffixes']

def main(argv):
	"""
		Pre_cleaner takes two mandatory arguments and several optional ones:

		"Usage: pre_cleaner.py -i <inputdir> -o <outputdir> [-c <chars_invalid>] [-b <bounday_chars>] 
		[-a <tokenized_chars>][-s <suffixes>] [-l <sentence_length>] [-t <token_length>] 
		[-x <sentence_symbols>] [-y <sentence_tokens>] [-z <token_symbols>] [-U] [-j] [-p] [-n] [-d] [-T] [-H] [-e] [-S]"

		inputdir 			Directory with files to be processed.
							Can contain subdirectories.
		outputdir			Directory to output processed files
		[
		chars_invalid		Characters to delete from text (default: none). They need to be given as a
							string without spaces between the characters, e.g. "$%^&" would eliminate
							only those 4 characters from appearances in the text.
		boundary_chars		Characters tokenized if token boundaries, only inside.
							Given as chars separated by space, e.g. "\" ' \."
							Default: apostrophe, double quote, dot
		tokenized_chars		Characters tokenized everywhere. Given as a string without spaces between 
							characters, e.g. "$%^&"
							Default: brackets, parenthesis, braces, comma, colon, semicolon, slash,
							currency signs, #, &, +, -
		suffixes 			Suffixes to eliminate in text (default: none). They need to come in a string
							separated by spaces.
							For example, -s "'s 'd n't" would eliminate all suffixes 's, 'd, n't
							As suffixes, they need to come at the end of a word to be eliminated
		sentence_length		Maximum sentence length accepted (default: 25). Sentences with more are deleted
		token_length 		Maximum token lenght accepted (default: 25). Tokens with more are deleted
		sentence_symbols	Symbols invalidating sentences (default: none). 
							Given as chars separated by space, e.g. "$ % ^ &" would eliminate
							all sentences that have those 4 characters.
		sentence_tokens 	Tokens invalidating sentences (default: none). They need to be given as a 
							string separated by spaces, e.g. "three invalid tokens" would eliminate all
							sentences including either "three", "invalid" or "tokens"
		token_symbols 		Symbols invalidating tokens (default: none).
							Given as chars separated by space, e.g. "$ % ^ &" would eliminate
							all sentences that have those 4 characters.
		-U 					Keep uppercase letters (default: convert to lowercase)
		-j 					Separate contractions (default: keep them together)
		-p 					Keep percentages (default: converts them to @percent@ token)
		-n 					Keep numbers (default: converts them to @number@ token)
		-d 					Keep dates (default: converts them to @date@ token)
		-T 					Keep times (default: converts them to @time@ token)
		-H 					Keep hyperlinks/emails (default: converts them to @url@/@email@ token)
		-e 					Keep escaped HTML and UniCode symbols (default: decodes them)
		-S 					Don't add sentence splitter mark to be recognized by
							split_sentences.pl, even if text is lowercased (they're added by default)
		]
	"""
	kwargs = {}
	try:
		opts, args = getopt.getopt(argv,"hi:o:c:b:a:s:l:t:x:y:z:UjpndTHeS",["idir=",
			"odir=", "chars_invalid=", "boundary_chars=","tokenized_chars=", 
			"suffixes=", "sen_length=", 
			"token_length=", "sentence_symbols=", "sentence_tokens=", 
			"token_symbols=" "Uppercase", "contractions", "percent",
			"numbers", "dates", 
			"Times", "Hyperlinks", "escaped", "Splits"])
	except getopt.GetoptError:
		print('''Usage: pre_cleaner.py -i <inputdir> -o <outputdir> 
		    [-c <chars_invalid>] [-b <boundary_chars>] [-a <tokenized_chars>] 
		    [-s <suffixes>] [-l <sentence_length] 
		    [-t <token_length>] [-x <sentence_symbols>] [-y <sentence_tokens>]
		    [-z <token_symbols>] [-U] [-j] [-p] [-n] [-d] [-T] [-H] [-e] [-S]''')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('''Usage: pre_cleaner.py -i <inputdir> -o <outputdir> 
			    [-c <chars_invalid>] [-b <boundary_chars>] [-a <tokenized_chars>] 
			    [-s <suffixes>] [-l <sentence_length] 
			    [-t <token_length>] [-x <sentence_symbols>] [-y <sentence_tokens>]
			    [-z <token_symbols>] [-U] [-j] [-p] [-n] [-d] [-T] [-H] [-e] [-S]''')
			sys.exit()
		elif opt in ("-i", "--idir"):
			inputdir = arg
		elif opt in ("-o", "--odir"):
			outputdir = arg
		elif opt in ("-c", "--chars_invalid"):
			kwargs['invalid_chars'] = arg
		elif opt in ("-b", "--boundary_chars"):
			kwargs['boundary_chars'] = arg
		elif opt in ("-a", "--tokenized_chars"):
			kwargs['tokenized_chars'] = arg
		elif opt in ("-s", "--suffixes"):
			kwargs['suffix_list'] = arg
		elif opt in ("-l", "--sen_length"):
			kwargs['max_tokens'] = int(arg)
		elif opt in ("-t", "--token_length"):
			kwargs['token_length'] = int(arg)
		elif opt in ("-x", "--sentence_symbols"):
			kwargs['sentence_invalid_symbols'] = arg
		elif opt in ("-y", "--sentence_tokens"):
			kwargs['sentence_invalid_tokens'] = arg
		elif opt in ("-z", "--token_symbols"):
			kwargs['token_invalid_symbols'] = arg
		elif opt in ("-U", "--Uppercase"):
			kwargs['convert_lowercase'] = False
		elif opt in ("-j", "--contractions"):
			kwargs['separate_contractions'] = True
		elif opt in ("-p", "--percent"):
			kwargs['convert_percent_to_tokens'] = False
		elif opt in ("-n", "--numbers"):
			kwargs['convert_numbers_to_tokens'] = False
		elif opt in ("-d", "--dates"):
			kwargs['convert_dates_to_tokens'] = False
		elif opt in ("-T", "--Times"):
			kwargs['convert_times_to_tokens'] = False
		elif opt in ("-H", "--Hyperlinks"):
			kwargs['convert_links_to_tokens'] = False
		elif opt in ("-e", "--escaped"):
			kwargs['decode_escaped'] = False
		elif opt in ("-S", "--Splits"):
			kwargs['add_splitters'] = False

	Execute_Precleaner(inputdir, outputdir, **kwargs)

def Execute_Precleaner(inputdir: str, outputdir: str, invalid_chars: str = "",
						boundary_chars: str = u'\' " \.', tokenized_chars: str = u"[](){}<>,:;/\$#&+=?!¡¿",
						suffix_list: str = "", max_tokens: int = 25, max_chars: int = 25, 
						sentence_invalid_symbols: str = "",	sentence_invalid_tokens: list = [],
						token_invalid_symbols: str = "", convert_lowercase: bool = True,
						separate_contractions: bool = False, convert_percent_to_tokens: bool = True,
						convert_numbers_to_tokens: bool = True, convert_dates_to_tokens: bool = True,
						convert_times_to_tokens: bool = True, convert_links_to_tokens: bool = True,
						decode_escaped: bool = True, add_splitters: bool = True):
	'''
	Pre-cleaner pipeline, calling the different transformation modules in the appropriate
	order to achieve desired cleanup
	'''
	for inputfile in os.listdir(inputdir):
		print("Processing: {}/{}".format(inputdir, inputfile))
		sentences = Load_Files(inputdir + "/" + inputfile)

		outputfile = outputdir + "/" + inputfile
		if not os.path.exists(outputdir):
		    os.makedirs(outputdir)

		fo = open(outputfile, "w")
		for sentence in sentences:
			temp_sentence = sentence
			if convert_links_to_tokens == True:
				temp_sentence = Substitute_Links(temp_sentence)
			if decode_escaped == True:
				temp_sentence = Decode_Escaped(temp_sentence)
			temp_sentence = Normalize_Sentence(temp_sentence, separate_contractions)
			if convert_dates_to_tokens == True:
				temp_sentence = Substitute_Dates(temp_sentence)
			if convert_times_to_tokens == True:
				temp_sentence = Substitute_Times(temp_sentence)
			if convert_percent_to_tokens == True:
				temp_sentence = Substitute_Percent(temp_sentence)
			if convert_numbers_to_tokens == True:
				temp_sentence = Substitute_Numbers(temp_sentence)
			new_suffix_list = Prepare_Suffix_List(suffix_list)
			temp_sentence = Clean_Sentence(temp_sentence, invalid_chars, new_suffix_list)
			temp_sentence = Char_Tokenizer(temp_sentence, boundary_chars, tokenized_chars)
			tokenized_sentence = Naive_Tokenizer(temp_sentence)
			if Ignore_Long_Sentence(tokenized_sentence, max_tokens) == True:
				continue
			tokenized_sentence = Remove_Long_Tokens(tokenized_sentence, max_chars)
			if Ignore_Invalid_Sentence(tokenized_sentence, sentence_invalid_symbols, sentence_invalid_tokens) == True:
				continue
			tokenized_sentence = Remove_Invalid_Tokens(tokenized_sentence, token_invalid_symbols)
			final_sentence = " ".join(tokenized_sentence) + "\n"
			if convert_lowercase == True:
				final_sentence = final_sentence.lower()
			if add_splitters == True:
				final_sentence = Add_Splitter(final_sentence)
			Write_Output_Sentence(fo, final_sentence)
		fo.close()

def Load_Files(filename):
	"""
		Loads file already sentence-splitted, returning a list of all sentences
	"""
	file = open(filename, "r")
	sentences = file.readlines()
	file.close()
	return sentences

def Add_Splitter(sentence):
	"""
		Add sentence splitter mark (newline) to be recognized by split_sentences.pl,
		even if text is lowercased.
	"""
	return sentence + "\n"

def Write_Output_Sentence(fo, sentence):
	"""
		writes sentence to the output file
	"""
	if not re.search(r"^\s*$", sentence):
		fo.write(sentence)

def Decode_Escaped(sentence):
	"""
		Converts found escaped HTML and unicode symbols to
		their printable version
	""" 
	#decode_sentence = bytes(sentence, 'ascii').decode('unicode-escape')

	# html escaped sequencues
	h = HTMLParser()
	#decode_sentence = h.unescape(decode_sentence)
	decode_sentence = h.unescape(sentence)

	return decode_sentence

def Char_Tokenizer(sentence, boundary_chars, tokenized_chars):
	"""
		Separates boundary_chars from the boundary of a word 
		and tokenized_chars from any part of the string
	"""
	tok_sentence = sentence
	# separates boundary_chars when they're found at word boundary
	for curr_char in boundary_chars.split():
		tok_sentence = re.sub(r"(\W|^)(" + curr_char + r"+)(\w)", r"\1 \2 \3", tok_sentence)
		tok_sentence = re.sub(r"(\w)(" + curr_char + r"+)(\W|$)", r"\1 \2 \3", tok_sentence)

	# separates all tokenized_chars
	trans_table = dict((ord(char), " " + char + " ") for char in tokenized_chars)
	tok_sentence = tok_sentence.translate(trans_table)

	return tok_sentence

def Naive_Tokenizer(sentence):
	"""
		Tokenizes sentence, naively splitting by space only.
		This is only for cleaning, a real tokenizer is suppossed to be applied
		later in the process.
	"""
	return sentence.split()

def Remove_Long_Tokens(tokenized_sentence, max_chars):
	"""
		Removes token from tokenized_sentence if token is longer than max_word_length
	"""
	short_word_sentence = [] + tokenized_sentence # forcing a copy, avoid pass by reference
	for token in tokenized_sentence:
		if len(token) > max_chars:
			short_word_sentence.remove(token)

	return short_word_sentence

def Ignore_Long_Sentence(tokenized_sentence, max_tokens):
	"""
		Determines if tokenized_sentence should be ignored, if it has more than max_tokens
	"""
	if len(tokenized_sentence) > max_tokens:
		return True
	else:
		return False

def Remove_Invalid_Tokens(tokenized_sentence, invalidating_symbols):
	"""
		Returns a tokenized sentence without tokens that include 
		invalidating_symbols
	"""
	valid_tokens_sentence = [] + tokenized_sentence # forcing a copy, avoid pass by reference
	for token in tokenized_sentence:
		for invalid_symbol in invalidating_symbols.split():
			if invalid_symbol in token:
				valid_tokens_sentence.remove(token)

	return valid_tokens_sentence

def Ignore_Invalid_Sentence(tokenized_sentence, invalidating_symbols, invalidating_tokens):
	"""
		Determines if tokenized_sentence should be ignored, 
		if it contains invalidating_tokens or invalidating_symbols 
	"""
	for token in tokenized_sentence:
		if token in invalidating_tokens:
			return True
	dummy = Remove_Invalid_Tokens(tokenized_sentence, invalidating_symbols)	
	if len(dummy) < len(tokenized_sentence):
		return True

	return False

def Clean_Sentence(sentence, invalid_chars, new_suffix_list):
	"""
		Cleans sentence from invalid chars
	"""
	# remove unaccepted characters
	translate_table = dict((ord(char), None) for char in invalid_chars)
	temp_sentence = sentence.translate(translate_table)
	# remove asterisk, so they are token-splitters
	temp_sentence = re.sub(r"\*", " ", temp_sentence)
	# remove long-dashes completely, so they are token-splitters
	temp_sentence = re.sub(r"—", " ", temp_sentence)
	# remove underscores completely, so they are token-splitters
	temp_sentence = re.sub(r"_", " ", temp_sentence)
	temp_sentence = Remove_Suffixes(temp_sentence, new_suffix_list)

	return temp_sentence

def Normalize_Sentence(sentence, separate_contractions):
	"""
		Converts all different apostrophes, double quotes and dashes to 
		standard symbols.
		Also removes underscores (commonly used as underline markup).
		Also separates contractions if separete_contractions
	"""

	# Normalize apostrophes, dashes and quotes obtained from Wikipedia 
	# Apostrophe page
	sentence = re.sub(r"`|’|‘", "'", sentence)
	# some dashes look the same, but they are different
	sentence = re.sub(r"‑|‐", "-", sentence)
	sentence = re.sub(r"-{2,}|―|—|–|‒", "—", sentence) 
	sentence = re.sub(r"''|“|”", '"', sentence)
	# remove underscores completely, so they are token-splitters
	# sentence = re.sub(r"_", " ", sentence)
	if separate_contractions == True:
		# separate contractions (e.g. They're -> They 're)
		sentence = re.sub(r"(?<=[a-zA-Z])(n'|')(?=[a-zA-Z])", r" \1", sentence)
	return sentence

def Substitute_Links(sentence):
	"""
		Substitutes url addresses (http://, https://, ftp://) with special token.
		Also, substitute emails to special token.
	"""
	link_pattern = r"\b(https?|ftp)://[^,\s]+"
	sentence = re.sub(link_pattern, ' @url@ ', sentence, flags=re.IGNORECASE) 
	email_pattern = r"(?<![^\s])[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?![^\s])"
	sentence = re.sub(email_pattern, ' @email@ ', sentence) 
	return sentence

def Substitute_Times(sentence):
	"""
		Substitutes time expressions with special token. 
		Formats taken from http://php.net/manual/en/datetime.formats.time.php
	"""
	#frac = r"(.[0-9]+)"
	hh = r"(0?[1-9]|1[0-2])"
	HH = r"([01][0-9]|2[0-4])"
	meridian = r"([AaPp]\.?[Mm]\.?)"
	MM = r"([0-5][0-9])"
	tz = r"(\(?[A-Za-z]{1,6}\)?|[A-Z][a-z]+([_/][A-Z][a-z]+)+)"
	tzcorrection = r"((GMT)?[+-]" + hh + ":?" + MM + "?)"
	tzalone = r"((GMT)[+-]" + hh + ":?" + MM + "?)"

	# Accepted time formats
	form1 = r"(\b" + hh + r"([.:]" + MM + r"){0,2}" + r" ?" + meridian + r"\b)"
	form2 = r"(\b" + HH + r"([.:]" + MM + r"){1,2}" + r" ?(" + tz + r"|" + tzcorrection + r")?\b)"
	form3 = r"(\b" + tzalone + r"\b)"

	time_pattern = form3 + r"|" + form2 + r"|" + form1 
	sentence = re.sub(time_pattern, ' @time@ ', sentence) 
	return sentence

def Substitute_Dates(sentence):
	"""
		Substitutes all dates with special token. Formats taken from http://php.net/manual/en/datetime.formats.date.php
	"""
	daysuf = r"(st|nd|rd|th)"
	dd = r"([0-2]?[0-9]|3[01])" + daysuf + r"?"
	DD = r"(0[1-9]|[1-2][0-9]|3[01])"
	m = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)"
	mm = r"(0?[0-9]|1[0-2])"
	y = r"(\d{1,4})"
	yy = r"(\d{2})"
	YY = r"(\d{4})"

	# Accepted date formats
	form1 = r"(\b" + mm + r"/" + dd + r"(/" + y + r")?\b)"
	form2 = r"(\b" + YY + r"/" + mm + r"/" + dd + r"\b)"
	form3 = r"(\b" + YY + r"-" + mm + r"(-" + dd + r")?\b)"
	form4 = r"(\b" + dd + r"[\.-]" + mm + "[\.-](" + YY + r"|" + yy + r")\b)"
	form5 = r"(\b" + dd + r"[ \.-]?" + m + r"([ \.-]?" + y + r")?\b)"
	form6 = r"(\b" + m + r"[ \.-]?" + YY + r"\b)"
	form7 = r"(\b" + YY + r"[ \.-]?" + m + r"\b)"
	form8 = r"(\b" + m + r"[,\. ]+" + y + r"\b)"
	form9 = r"(\b" + m + r"[ \.-]?" + dd + r"[,\. ]+(" + y + r")?(\b| |$))"
	form10 = r"(\b" + m + r"-" + DD + r"-" + y + r"\b)"
	form11 = r"(\b" + y + r"-" + m + r"-" + DD + r"\b)"

	date_pattern = form11 + r"|" + form10 + r"|" + form9 + r"|" + form8 + r"|" + form7 + r"|" + form6 + r"|" + form5 + r"|" + form4 + r"|" + form3 + r"|" + form2 + r"|" + form1
	sentence = re.sub(date_pattern, ' @date@ ', sentence, flags=re.IGNORECASE) 
	return sentence

def Substitute_Percent(sentence):
	"""
		Substitutes percents with special token
	"""
	sentence = re.sub(r'''(?<![^\s"'[(])[+-]?[.,;]?(\d+[.,;']?)+%(?![^\s.,;!?'")\]])''', 
' @percent@ ', sentence)
	return sentence


def Substitute_Numbers(sentence):
	"""
		Substitutes numbers with special token
	"""
	# handles trailing/leading decimal mark
	sentence = re.sub(r'''(?<![^\s"'[(])[#+-]?[.,;]?(\d+[.,;']?)*(\d+[.,;]?)(?![^\s!?'")\]])''',
	 			       ' @number@ ' , sentence)
	return sentence

def Prepare_Suffix_List(suffix_list):
	"""
		Adds regular expression parts to given suffixes
	"""
	new_suffix_list = []
	for suffix in suffix_list.split():
		regex_suffix = r"(?<=\w)" + suffix + r"(?=\s)"
		new_suffix_list = new_suffix_list + [regex_suffix]
	return new_suffix_list

def Remove_Suffixes(sentence, suffix_list):
	"""
		Removes suffixes in the list from the sentence
	"""
	for suffix in suffix_list:
		sentence = re.sub(suffix, "", sentence)
	return sentence

if __name__ == "__main__":
	main(sys.argv[1:])

