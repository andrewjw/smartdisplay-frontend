#!/bin/bash

ampy ${@:1} mkdir smartdisplay --exists-okay
ampy ${@:1} put smartdisplay/ smartdisplay/

ampy ${@:1} mkdir images --exists-okay
ampy ${@:1} put images/ images/

ampy ${@:1} put main.py main.py
