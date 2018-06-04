from setuptools import setup

setup(name='opencog-ull',
      version='1.0.0',
      description='Unsupervised Language Learning Toolkit',
      author='Opencog ULL Team',
      url='http://github.com/singnet/language-learning',
      packages=['grammartest'],
      package_dir={'grammartest': 'src/link_grammar'},
      platform='any',
      license='MIT',
      classifiers=[
          'Development Status :: 1 - Alpha',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          # 'Topic :: Communications :: Email',
          # 'Topic :: Office/Business',
          'Topic :: Software Development :: Bug Tracking',
          ],
      long_description=open('README.md').read()
      )