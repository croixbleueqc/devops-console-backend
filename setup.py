#!/usr/bin/env python3

# Copyright 2019 mickybart
# Copyright 2020 Croix Bleue du Québec

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Setup module
'''

from setuptools import setup, find_packages, Command

import os
import subprocess

def execute(cmd):
    proc = subprocess.run(cmd)
    proc.check_returncode()

class InitCommand(Command):
    description="Initialize and Configure the template"

    user_options = [
        ("name=", None, "Project name"),
        ("desc=", None, "Project description"),
        ("rm-helloworld", "c", "Remove helloworld"),
        ("git-commit", "g", "Commit for me")
    ]

    def initialize_options(self):
        self.name = None
        self.desc = None
        self.rm_helloworld = 0
        self.git_commit = 0

    def finalize_options(self):
        if self.name is None:
            raise Exception("Parameter --name is missing")
        if self.desc is None:
            raise Exception("Parameter --desc is missing")

    def run(self):
        print(" => Initializing the template ...")

        if self.rm_helloworld == 1:
            print("    - Remove helloworld")
            os.remove("svc/apis/helloworld.py")
            os.remove("svc/core/helloworld.py")
            execute(
                [
                    "sed",
                    "-i",
                    "/helloworld/d",
                    "svc/core/core.py",
                    "svc/apiv1.py"
                ]
            )

        print("    - Setting project name and description")
        execute(
            [
                "sed",
                "-i",
                "s/PROJECT_NAME/{}/;s/$PROJECT_DESC/{}/".format(self.name, self.desc),
                "svc/config/default.json"
            ]
        )
        execute(
            [
                "sed",
                "-i",
                "s/'devops_console'/'{}'/;s/'DevOps Console Backend'/'{}'/".format(self.name, self.desc),
                "setup.py"
            ]
        )
        execute(
            [
                "sed",
                "-i",
                "s/svc/{}/g".format(self.name),
                "Dockerfile",
                "tests/test_service.py",
                "MANIFEST.in"
            ]
        )

        print("    - Renaming svc module to {}".format(self.name))
        os.rename("svc", self.name)

        if self.git_commit == 1:
            print("    - Commit")
            execute(["git", "add", "."])
            execute(["git", "commit", "-m", "Initialize the service"])

        print("  > done")

class BootstrapCommand(Command):
    description="Bootstrap"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print(" => bootstrapping development environment ...")

        execute(["pip", "install", "--user", "-e", "."])

        print("  > done")

setup(
    name='devops_console',
    description='DevOps Console Backend',
    url='',
    version='0.2.2',
    python_requires='>=3.7',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'aiohttp[speedups]',
        'aiohttp-swagger',
        'prometheus_async[aiohttp]',
    ],
    extras_require={
        'dev': [
            'pylint',
            'pytest-cov',
            'bumpversion',
        ],
        'prod': [
            'gunicorn',
        ],
    },
    test_suite="tests",
    include_package_data=True,

    # Metadata
    author='Croix Bleue du Quebec',
    author_email='devops@qc.croixbleue.ca',
    license='LGPL-3.0-or-later',
    long_description=open('README.md').read(),
    keywords=["devops", "backend"],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match 'license' above)
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',

        'Operating System :: OS Independent',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # Custom command
    cmdclass={
        'init': InitCommand,
        'bootstrap': BootstrapCommand,
    },
)
