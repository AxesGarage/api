#!/bin/bash
source bin/activate;
python history.py &
exec gunicorn -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log main:app;
