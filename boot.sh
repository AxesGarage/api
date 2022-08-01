#!/bin/bash
source bin/activate;
python history.py reset &>/dev/null & disown;
exec gunicorn -b 0.0.0.0:5000 --access-logfile access.log --error-logfile error.log main:app;