#! /bin/sh

cd "$1" || exit 1
git blame "$3"~ --porcelain -L "$4","$5" -- "$2"