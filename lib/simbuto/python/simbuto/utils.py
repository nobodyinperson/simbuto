#!/usr/bin/env python3
import os
import re

# split a path into its components
def splitpath(path):
    res = []
    # split the path
    while True:
        base, subject = os.path.split(path)
        if path == base:
            break
        else:
            if subject: res.append(subject) 
        path = base
    res.reverse()
    return res


