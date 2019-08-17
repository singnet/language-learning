#!/bin/bash
# Removes first field at the beginning of every block in passed file(s).
# Useful for cleaning ull files by DNN with initial LEFT-WALL.

# Takes one argument: file or directory with files to remove LW
# Outputs processed files in directory with same name, appended by "-OLW"

# usage: rm_LEFTWALL.sh <file or dir>

newdir="${1%/}-0LW";
echo "Results written in folder $newdir:"
mkdir -p $newdir;

if [ -d "$1" ]
then
	for file in $1/*
	do
	    filename=$(basename -- "$file");
	    echo $filename;
		uniq $file | awk -v RS='\n\n' 'sub("^" $1 FS, _) {print $0 "\n"}' > $newdir/$filename;
	done
elif [ -f "$1" ]
then
	echo $1
	uniq $1 | awk -v RS='\n\n' 'sub("^" $1 FS, _) {print $0 "\n"}' > $newdir/$1;
else echo "$1 is not valid";
	exit 1;
fi

# uniq removes all duplicated newlines
# awk 	-v RS defines the record separator as an empty line
#		then awk removes first field at the beginning of the block