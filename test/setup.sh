#!/bin/bash

dir="$1"
init_branch=test_main
cd "$dir"

git init -b "$init_branch"

echo 'Hello, world!' >a.txt
git add a.txt
git commit -m '1st commit'

echo 'Hey there!' >b.txt
git add b.txt
git commit -m '2nd commit'

echo 'Come here often?' >>a.txt
git add a.txt
git commit -m '3rd commit'

git rm b.txt
git commit -m '4th commit'

for branch in foo bar baz quux; do
    git checkout -b "$branch"
    echo "Editing on branch $branch" >c.txt
    git add c.txt
    git commit -m "Edit c.txt on branch $branch"
    git checkout "$init_branch"
done