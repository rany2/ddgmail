from pkg_resources import parse_version
from setuptools import __version__ as setuptools_version
from setuptools import setup

min_setuptools_version = "42.0.0"
# This conditional isn't necessary, but it provides better error messages to
# people who try to install this package with older versions of setuptools.
if parse_version(setuptools_version) < parse_version(min_setuptools_version):
    raise RuntimeError(f"setuptools {min_setuptools_version}+ is required")

setup(
    name="ddgmail",
    version="0.1.5",
    py_modules=["ddgmail"],
    author="rany",
    author_email="ranygh@riseup.net",
    url="https://github.com/rany2/ddgmail",
    description="A command line tool to use DuckDuckGo's E-mail forwarding service",
    install_requires=[
        "Click",
        f"setuptools>={min_setuptools_version}",
    ],
    entry_points={
        "console_scripts": [
            "ddgmail = ddgmail:cli",
        ],
    },
    classifiers={
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    },
)
