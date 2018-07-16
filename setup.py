from setuptools import setup, find_packages

def readme():
    with open("README.md") as f:
        return f.read()

def license():
    with open("LICENSE") as f:
        return f.read()


reqs = [line.strip() for line in open("requirements.txt")]

GIT_REPO = "https://github.com/cedadev/compliance-check-spec"

setup(
    name                 = "compliance-check-spec",
    version              = "0.0.1",
    description          = "Specification writer for compliance checker",
    long_description     = readme(),
    license              = license(),
    url                  = GIT_REPO,
    packages             = find_packages(),
    install_requires     = reqs,
    tests_require        = ["pytest"],
    classifiers          = [
        "Development Status :: 2 - ???",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: BSD 3-Clause License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
    ],
    include_package_data = True,
    scripts=[],
    entry_points         = {
        "console_scripts": [
            "write-spec=compliance_check_spec.spec_writer:main",
        ]
    },
)
