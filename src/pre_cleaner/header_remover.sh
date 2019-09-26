#!/bin/bash
#
# ASuMa, June 2018
# Removes header and footer from Gutenberg's Books
# Run where you have the folder with files to process

# Usage: <PATH>/header_remover.sh inputDIR outputDIR

for file in $PWD/$1/*
do
	echo "Processing file ${file}"

    X="$(sed -rn '/\*\*\*\s?START OF TH/=' $file)"
    if [ "$X" = "" ];
    then X=0;
	fi
	((X++))

    Y="$(sed -rn '/\*\*\*\s?END OF TH/=' $file)"
    if [ "$Y" = "" ];
    then Y=1000000;
	fi
	((Y--))

	filename=$(basename -- "$file")
	mkdir -p $2

	sed -n -e "$X,$Y p" -e "$Y q" $file > "${2}/${filename}"
	#tail -n +"$start_line" $file | head -n "$((start_line - end_line))" > trash
done
