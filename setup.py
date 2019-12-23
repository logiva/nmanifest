import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nmanifest",
    version="0.0.2",
    author="Steffen Vinther Sørensen",
    author_email="svs@logiva.dk",
    description="Generate dynamic number of manifest repetitions using minimum configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/logiva/nmanifest",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "dict-recursive-update>=1.0.1",
        "Jinja2>=2.10.3",
        "MarkupSafe>=1.1.1",
        "oyaml>=0.9"
    ],
    python_requires='>=3.5',
)
