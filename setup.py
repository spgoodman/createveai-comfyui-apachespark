from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='createveai-apachespark',
    version='0.1.0',
    description='Apache Spark nodes for ComfyUI with advanced data processing and feature extraction capabilities',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='CreateveAI',
    author_email='support@createve.ai',
    url='https://github.com/createveai/createveai-apachespark',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.2.0',
            'myst-parser>=2.0.0',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'createveai-apachespark=createveai_apachespark.cli:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/createveai/createveai-apachespark/issues',
        'Source': 'https://github.com/createveai/createveai-apachespark',
        'Documentation': 'https://createveai-apachespark.readthedocs.io/',
    },
    keywords=[
        'comfyui',
        'apache-spark',
        'machine-learning',
        'data-processing',
        'feature-extraction',
        'stable-diffusion',
        'databricks',
        'deep-learning',
        'artificial-intelligence',
    ],
)
