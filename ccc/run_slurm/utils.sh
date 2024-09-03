#!/bin/bash

function cleanup() {
  echo "Terminated. Cleaning up .."
  kill 0
}

function wait_or_interrupt() {  
  trap cleanup SIGINT
  # now wait
  if [ -z "$1" ] ; then
    wait
  else
    # wait if more child processes exist than allowed ($1 is the number of allowed children)
    while test $(jobs -p | wc -w) -ge "$1"; do wait -n; done
  fi
}