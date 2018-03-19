import codecs
import os
import re
import sys

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


long_description = read('README.md')

tests_require = [
    'flask',
    'pexpect',
]


setup(
    name="ssh_metro_server",
    version=find_version("sshmetroserver", "__init__.py"),
    description="An SSH tunnel server.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy"
    ],
    keywords='python pexpect ssh flask tunnel ssh-tunnel',
    author='thilux (Thiago Santana)',
    author_email='thilux.systems@gmail.com',
    license='Apache 2',
    package_dir={"": "."},
    packages=find_packages(
        where=".",
        exclude=["contrib", "docs", "tests*", "tasks"],
    ),

    entry_points={
        "console_scripts": [
            "ssh_metro_server=sshmetroserver.main:main"
        ],
    },
    tests_require=tests_require,
    zip_safe=False,
    python_requires='>=3.6',
    extras_require={
        'testing': tests_require,
    },
)