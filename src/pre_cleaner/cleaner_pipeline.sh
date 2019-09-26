#!/bin/bash

# ASuMa, June 2018
# Usage: cleaner_pipeline.sh <inputdir> <outputdir> [more args to run_cleaner]
# Run from directory above your inputdir
# Runs header_remover.sh, followed by run_cleaner.sh

CLEANER_PATH="`dirname \"$0\"`"

HEADLESS_DIR=headless-books

mkdir -p $HEADLESS_DIR

$CLEANER_PATH/header_remover.sh $1 $HEADLESS_DIR

shift
$CLEANER_PATH/run_cleaner.sh $HEADLESS_DIR $@
