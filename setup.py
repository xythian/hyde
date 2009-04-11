from distutils.core import setup, Command
from distutils.command.install import INSTALL_SCHEMES

import os

try:
    import py
except ImportError:
    py = False

class PyTestCommand(Command):
    description = 'Run package tests with py.test'
    user_options = []
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
        
    def run(self):
        if not py:
            print "Tests require py lib:  http://codespeak.net/py/dist/download.html"
            return
        
        tests = ['tests/%s' % t for t in os.listdir('tests') if t.endswith('.py') and t.startswith('test_')]

        # This bit is more or less copied from  the py.test runner in py/test/cmdline.py
        config = py.test.config
        config.parse(tests) 
        config.pytestplugins.do_configure(config)
        session = config.initsession()
        exitstatus = session.main()
        config.pytestplugins.do_unconfigure(config)
        raise SystemExit(exitstatus)


for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

data_files = []
for dirpath, dirnames, filenames in os.walk('hydeengine/templates'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): 
            del dirnames[i]
    if filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

#import pprint
#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(data_files)
#import sys
#sys.exit(1)

setup(
    name='hyde',
    version='0.3b',
    author='Lakshmi Vyas',
    author_email='lakshmi.vyas@gmail.com',
    url='http://www.ringce.com/products/hyde/hyde.html',
    description='Static website generator using Django templates',

    packages=['hydeengine'],
    scripts=['scripts/hyde.py',],
      data_files=data_files,
#    package_data={'templates': ['templates/*']},

    cmdclass = {'test': PyTestCommand},
    )
