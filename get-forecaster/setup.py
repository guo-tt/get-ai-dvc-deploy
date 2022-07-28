from setuptools import setup, find_packages

setup(
    name="get-forecaster",
    version="0.1.0",
    # py_modules=["porter.portercli"],
    include_package_data=True,
    pacakge_dir={"": "src"},
    package_data={
        "forecaster": ["config/*"]
    },
    packages=find_packages(),
    install_requires=[
    ],
)
