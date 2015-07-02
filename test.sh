#!/usr/bin/env sh

FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -e '\.py$')

    if [ -n "$FILES" ]; then
        flake8 -r $FILES
    fi
