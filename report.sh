#!/bin/bash
todo="enabled"

echo "Running url check..."
./urlcheck.py
myrc=$?
if [ $myrc -ne 0 ]; then
  echo "disable loadbalancer"
  todo="disable"
fi

echo Running package check...
./packcheck.py
myrc=$?

if [ $myrc -ne 0 ]; then
  echo "disable loadbalancer"
  todo="disable"
fi

echo service loadbalancer $todo
