import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="marcel-the-bot",
    version="3.4.1",
    author="akrocynova",
    author_email="",
    description="Marcel the Discord Bot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hoot-w00t/marcel-the-bot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "marcel-the-bot=marcel:main"
        ]
    },
    install_requires=[
        "discord.py[voice]==1.5.0",
        "youtube-dlc"
    ],
    python_requires='>=3.6',
)