from setuptools import setup, find_packages

setup(
    name="srm_portal",
    version="1.0",
    # THE FIX: By removing the 'package_dir' restriction, find_packages()
    # natively scans your entire Git root. It will dynamically discover
    # 'App', 'frontend', and any future folders you ever create!
    packages=find_packages(),
)
