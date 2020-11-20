#!/bin/bash

# This script was used Nov 2020 for the evaluation in the ADC talk.

# big run
hyperfine --warmup 5 --min-runs 50 \
    'dawtool ./als/als0.als -m' 'dawtool ./als/als10.als -m' \
    'dawtool ./als/als100.als -m' 'dawtool ./als/als1000.als -m' \
    'dawtool ./fl/flp0.flp -m' 'dawtool ./fl/flp10.flp -m' \
    'dawtool ./fl/flp100.flp -m' 'dawtool ./fl/flp1000.flp -m' \
    --export-csv run9-1-scipyfast.csv --export-json run9-1.json

hyperfine --warmup 1 --min-runs 5 \
    'dawtool ./als/als10000.als -m' 'dawtool ./als/als100000.als -m' \
    'dawtool ./fl/flp10000.flp -m' 'dawtool ./fl/flp100000.flp -m' \
    --export-csv run9-2-scipyfast-huge.csv --export-json run9-2.json


# little test
# hyperfine --warmup 5 --min-runs 10 \
#     'dawtool ./als/als0.als -m' 'dawtool ./als/als10.als -m' \
#     'dawtool ./als/als100.als -m' 'dawtool ./als/als1000.als -m' \
#     'dawtool ./fl/flp0.flp -m' 'dawtool ./fl/flp10.flp -m' \
#     'dawtool ./fl/flp100.flp -m' 'dawtool ./fl/flp1000.flp -m' \
