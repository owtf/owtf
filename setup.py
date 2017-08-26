import os
import sys
from subprocess import call

import pip

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

from setuptools.command.develop import develop
from setuptools.command.install import install


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

links = []
requires = []

# new versions of pip requires a session
requirements = pip.req.parse_requirements('requirements.txt', session=pip.download.PipSession())

for item in requirements:
    if getattr(item, 'url', None):  # older pip has url
        links.append(str(item.url))
    if getattr(item, 'link', None):  # newer pip has link
        links.append(str(item.link))
    if item.req:
        requires.append(str(item.req))  # always the package name

post_script = os.path.join(ROOT_DIR, "owtf/install/install.py")

tests_require = [
    'PyHamcrest==1.9.0',
    'mock>=1.3.0',
    'pytest==3.2.1'
]


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # Need because of a setuptools bug: https://github.com/pypa/setuptools/issues/456
        self.do_egg_install()
        print('Running post install')
        call([sys.executable, post_script])


setup(
    name='owtf',
    version="2.1",
    url='https://github.com/owtf/owtf',
    license='BSD',
    author="Abraham Aranguren",
    author_email="abraham.aranguren@owasp.org",
    description='OWASP+PTES focused try to unite great tools and make pen testing more efficient',
    long_description="OWASP OWTF is a project focused on penetration testing efficiency and alignment of security tests"
                     "to security standards like the OWASP Testing Guide (v3 and v4), the OWASP Top 10, PTES and NIST",
    packages=find_packages(exclude=['*node_modules/*']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=sorted(requires, key=lambda s: s.lower()),
    dependency_links=links,
    extras_require={
        'test': tests_require,
    },
    cmdclass={
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'owtf = owtf.__main__:main'
        ]
    }
)
