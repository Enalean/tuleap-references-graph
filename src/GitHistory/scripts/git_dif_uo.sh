#! /bin/sh

cd "$1" || exit 1
git diff "$2"~ "$2" -U0