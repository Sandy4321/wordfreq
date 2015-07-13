from setuptools import setup

setup(
    name="wordfreq_builder",
    version='0.1',
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='info@luminoso.com',
    url='http://github.com/LuminosoInsight/wordfreq_builder',
    platforms=["any"],
    description="Turns raw data into word frequency lists",
    packages=['wordfreq_builder'],
    install_requires=['msgpack-python', 'pycld2'],
    entry_points={
        'console_scripts': [
            'wordfreq-pretokenize-twitter = wordfreq_builder.cli.pretokenize_twitter:main',
            'wordfreq-format-twitter = wordfreq_builder.cli.format_twitter:main',
            'wordfreq-build-deps = wordfreq_builder.cli.build_deps:main'
        ]
    }
)
