#!/bin/bash
echo "startup backend api"
echo "slight sleep to allow database to setup"
sleep 2
echo "run database commands and then the actual api"
flask db upgrade
python age_of_gold.py
