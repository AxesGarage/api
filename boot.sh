#!/bin/bash
source bin/activate
exec gunicorn -b 0.0.0.0:5000 --access-logfile access.log --error-logfile error.log main:app