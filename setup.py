from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='libezgripper',
    version='1.3.0',
    description='A driver for EZGripper',
    long_description=long_description,

    url='https://github.com/SAKErobotics/libezgripper',
    author='SAKE Robotics',
    author_email='',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='robot gripper driver',

    packages=find_packages(),
)

