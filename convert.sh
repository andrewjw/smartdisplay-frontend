#!/bin/bash

set -e

mkdir -p images

i75-convert-image raw_images/train_home.png 1 > images/train_home.i75
i75-convert-image raw_images/train_to_london.png 1 > images/train_to_london.i75
i75-convert-image raw_images/cloudy.jpg 3 > images/cloudy.i75
i75-convert-image raw_images/cold.jpg 3 > images/cold.i75
i75-convert-image raw_images/hot.jpg 3 > images/hot.i75
i75-convert-image raw_images/rainy.jpg 3 > images/rainy.i75
i75-convert-image raw_images/sunrise.jpg 3 > images/sunrise.i75
i75-convert-image raw_images/night.jpg 3 > images/night.i75
i75-convert-image raw_images/sunny.jpg 3 > images/sunny.i75
