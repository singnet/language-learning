#!/bin/bash
# Counts number of parses in files, based on newlines.
# Takes one arguments: file to count parses, or directory containing
# files to count parses.
# If directory is given as argument, it counts parses for each
# individual file inside the directory, and also gives a grand total.

# usage: parse_counter.sh <file or dir>

if [ -d "$1" ]
then 
	for file in $1/*
	do
	    echo "Counts for $file";
	    uniq $file | grep -cvP '\S';
	done
	echo "Counts for whole directory:";
	cat $1/* | uniq | grep -cvP '\S';
elif [ -f "$1" ]
then 
	echo "Counts for $1";
	uniq $1 | grep -cvP '\S';
else echo "$1 is not valid";
	exit 1;
fi