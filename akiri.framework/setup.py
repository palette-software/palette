from setuptools import setup

setup(
    name = "akiri.framework",
    version = "0.5.6",
    author = "Akiri Solutions, Inc",
    author_email = "development@akirisolutions.com",
    maintainer = "Palette Developers",
    maintainer_email = "developers@palette-software.com",
    description = ("Akiri Web Framework"),
    long_description = ("Akiri Web Framework for web application development"),
    url = "http://www.akirisolutions.com",
    packages=[
        "akiri",
        "akiri.framework",
        "akiri.framework.middleware",
        "akiri.framework.profile",
        "akiri.framework.profile.store",
        "akiri.framework.servers",
        "akiri.framework.sqlalchemy"
    ],
    package_data={
        'akiri.framework.servers': ['utils/*']
    },
    install_requires=[
        "WebOb",
        "Paste>=1.7.5",
        "sqlalchemy>=0.7"
    ]
)
