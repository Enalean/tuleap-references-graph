#! /bin/sh

cd "$1" || exit 1
git log "$2" -n 1 --format=format:"%B"