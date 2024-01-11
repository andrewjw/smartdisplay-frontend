#!/bin/bash

set -e

mkdir -p images

i75-convert-image raw_images/train_home.png 1 > images/train_home.i75
i75-convert-image raw_images/train_to_london.png 1 > images/train_to_london.i75
