import sys, os, bottle

sys.path = [os.path.dirname(__file__)] + sys.path
os.chdir(os.path.dirname(__file__))

import performance # This loads your application

application = bottle.default_app()
