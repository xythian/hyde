from distutils.core import setup, Command
import os

class TestCommand(Command):
    description = 'Run package tests'
    user_options = []
    
    def __init__(self, dist):
        Command.__init__(self, dist)
        self._dir = os.getcwd()

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
        
    def run(self):
        print "I don't actually know how to run these tests yet, so..."
                

setup(name='hyde',
      version='0.3b',
      author='Lakshmi Vyas',
      author_email='lakshmi.vyas@gmail.com',
      url='http://www.ringce.com/products/hyde/hyde.html',
      description='Static website generator using Django templates',

      packages=['hydeengine'],
      scripts=['scripts/hyde.py',],
      
      cmdclass = {'test': TestCommand},
      )
