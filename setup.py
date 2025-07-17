# encoding=utf8
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements
    
# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
REQS = [str(ir.requirement) for ir in install_reqs]

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
README = read('README.rst')

class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)

setup(
    name = "django-media-tree",
    version = "0.9.0",
    install_requires=REQS,
    url = 'http://github.com/samluescher/django-media-tree',
    license = 'BSD',
    description="Django Media Tree is a Django app for managing your website's "
                "media files in a folder tree, and using them in your own applications.",
    long_description = README,

    author = u'Samuel Luescher',
    author_email = 'sam at samluescher dot net',

    packages = find_packages(),
    include_package_data=True,

    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
    ],

    tests_require=['tox'],
    cmdclass={'test': Tox},
)
