import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='terraecs',
    version='1.0.0',
    author='Gunter Grodotzki',
    author_email='gunter@grodotzki.co.za',
    description='A simple Fargate after Terraform runner.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lifeofguenter/terraecs',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3',
    install_requires=[
      'boto3',
      'click',
    ],
    entry_points={
        'console_scripts': [
            'terraecs = terraecs.__main__:cli',
        ],
    },
)
