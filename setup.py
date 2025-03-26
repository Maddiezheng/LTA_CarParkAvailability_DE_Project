# 在项目根目录创建setup.py
import setuptools

setuptools.setup(
    name='carpark-pipeline',
    version='0.1',
    install_requires=[
        'apache-beam[gcp]>=2.53.0',
        'confluent-kafka>=2.0.0',
    ],
    packages=setuptools.find_packages(),
)