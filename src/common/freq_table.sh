#!/bin/bash
# creates frequency table for words in file
# takes two arguments: corpus and otuput file name

# usage: ./freq_table.sh corpus output

tr " " "\n" < $1 | sort | uniq -c | awk '{print $2"\t"$1}' | sort -k 2,2 -r -n > $2
