from distutils.core import setup

setup(name='hyde',
      version='0.3b',
      author='Lakshmi Vyas',
      author_email='lakshmi.vyas@gmail.com',
      url='http://www.ringce.com/products/hyde/hyde.html',
      description='Static website generator using Django templates',

      packages=['hydeengine'],
      scripts=['scripts/hyde.py',],
      )
