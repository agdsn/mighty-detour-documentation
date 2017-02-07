#!/bin/bash
for i in $(seq 1 30)
do
        python3 server.py $((9000 + i)) &
done
