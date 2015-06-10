from setuptools import setup, find_packages


setup(
    name = 'Astro',
    version = 0.1,
    description = 'Experiments with astronomical calculations',
    author = 'Mark Sundstrom',
    author_email = 'mark@mhsundstrom.com',
    url = 'https://github.com/mhsundstrom/astro',
    packages = ['home'],
    include_package_data=False,
    requires=['skyfield'],
    zip_safe=False,
    scripts = [],
    entry_points={
        'console_scripts': [
            ',astro=home.__main__:current',
        ],
    },
)
