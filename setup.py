import codecs
import os
from subprocess import call

from setuptools import setup, find_packages

from setuptools.command.develop import develop
from setuptools.command.install import install


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

# Extracts the version details
def get_version(init_path):
    # Read the __init__ file
    with open(init_path, "r+") as f:
        init_page = f.read()
    # Extract the version from the init file
    for each_line in init_page.splitlines():
        if each_line.startswith("__version__"):
            delimiter = '"' if '"' in each_line else "'"
            return each_line.split(delimiter)[1]


def strip_comments(l):
    return l.split("#", 1)[0].strip()


def _pip_requirement(req):
    if req.startswith("-r "):
        _, path = req.split()
        return reqs(*path.split("/"))
    return [req]


def _reqs(*f):
    return [
        _pip_requirement(r)
        for r in (
            strip_comments(l)
            for l in open(os.path.join(os.getcwd(), "requirements", *f)).readlines()
        )
        if r
    ]


def reqs(*f):
    return [req for subreq in _reqs(*f) for req in subreq]


# Absolute path for README.md
readme_md = read_me = os.path.join(ROOT_DIR, "README.md")

# Long description
long_description = codecs.open(os.path.abspath("README.md"), "r", "utf-8").read()

post_script = os.path.join(ROOT_DIR, "scripts/install.sh")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)
        print("Running post install")
        call(["/bin/bash", post_script])


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        # Need because of a setuptools bug: https://github.com/pypa/setuptools/issues/456
        self.do_egg_install()
        print("Running post install")
        call(["/bin/bash", post_script])


setup(
    name="owtf",
    version=get_version("owtf/__init__.py"),
    url="https://github.com/owtf/owtf",
    license="BSD",
    author="Abraham Aranguren",
    author_email="abraham.aranguren@owasp.org",
    description="OWASP+PTES focused try to unite great tools and make pen testing more efficient",
    long_description=long_description,
    packages=find_packages(exclude=["node_modules", "node_modules.*"]),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=reqs("base.txt") + reqs("docs.txt"),
    # test_requires=reqs("test.txt"),
    cmdclass={"develop": PostDevelopCommand, "install": PostInstallCommand},
    scripts=["bin/owtf"],
    entry_points={"console_scripts": ["owtf=owtf.core:main"]},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: POSIX :: Linux",
        "Topic :: Security",
    ],
)
