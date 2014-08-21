from setuptools import setup, find_packages

version = '0.9.4'

setup(name='palette',
    version=version,
    description="Main Palette UI application.",
    long_description="",
    classifiers=[],
    keywords="",
    author="",
    author_email="",
    url="",
    license="",
    packages=['palette'],
    include_package_data=True,
    package_data={
        'palette':
	    ['templates/*', 'data/*',
             'images/*', 'img/*',
             'js/*.js', 'js/templates/*', 'css/*.css', 'js/vendor/*.js',
             'fonts/svgs/*', 'fonts/*.eot', 'fonts/*.svg', 'fonts/*.tff', 'fonts/*.woff', 'fonts/*.css', 'fonts/webfonts/*.woff', 'fonts/webfonts/*.ttf']
        },
    data_files = [],
    zip_safe=False,
    install_requires=[
      # Extra requirements go here #
    ],
    entry_points="""
    [akiri.framework]
    akiri.plugin = palette
    """,
)
