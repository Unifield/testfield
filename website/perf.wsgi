import sys, os
import os.path

os.environ['MPLCONFIGDIR'] = "/tmp"

path = "~/.myenv/bin/activate_this.py"
activate_env = os.path.expanduser(path)
execfile(activate_env, dict(__file__=activate_env))

import bottle

sys.path = [os.path.dirname(__file__)] + sys.path
os.chdir(os.path.dirname(__file__))

import performance # This loads your application

application = bottle.default_app()
