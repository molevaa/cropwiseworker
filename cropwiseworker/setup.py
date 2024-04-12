from setuptools import setup, find_packages

def readme():
  with open('README.md', 'r') as f:
    return f.read()

setup(
  name='cropwiseworker',
  version='0.0.1',
  author='Molev Arkhip',
  author_email='jobarkhip@gmail.com',
  description='Модуль реализует функции для работы с API цифровой платформы управления агропредприятием Cropwise Operations.',
  long_description=readme(),
  long_description_content_type='text/markdown',
  packages=find_packages(),
  install_requires=['requests','pandas'],
  classifiers=[
    'Programming Language :: Python :: 3.11',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent'
  ],
  keywords='cropwise',
  python_requires='>=3.7'
)
