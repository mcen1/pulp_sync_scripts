#!/bin/env python
# load a file and return a dictionary

def file2dict(myfile):
  dicts_from_file = {}
  with open(myfile,'r') as inf:
    for line in inf:
      dicts_from_file=eval(line)
  return dicts_from_file
