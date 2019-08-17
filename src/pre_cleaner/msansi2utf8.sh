#!/bin/bash
#
# USE ONLY ON FILES THAT ARE IDENTIFIED AS CODED IN MS-ANSI (CP1252)

# ASuMa, June 2018
# Replaces some MS-ANSI (CP1252) chars for the UTF-8 equivalent

# Usage: <PATH>/msansi2utf8.sh inputDIR outputDIR

for file in $PWD/$1/*
do
	echo "Processing file ${file}"

	filename=$(basename -- "$file")
	mkdir -p $2

	sed -r "s/\x91/'/g; s/\x92/'/g; s/\x93/\"/g; s/\x94/\"/g" $file > "${2}/${filename}"
done
