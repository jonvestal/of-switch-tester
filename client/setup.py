from setuptools import find_packages, setup

setup(
    name='switch-tester',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'oftester = oftester.switch_test_runner:main',
        ],
    },
    install_requires=[
        'jinja2',
        'requests',
        'PyYAML',
        'plotly'
    ],
    extras_require={
        'test': [
            'pytest'
        ],
    },
)