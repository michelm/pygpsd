#!/bin/bash
set -e

dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd $dir

rm -rf dist build *.egg-info
python3 setup.py sdist bdist_wheel

pkg=`find dist -type f -name 'pygpsd*.whl' -exec basename {} \;`
version=`echo $pkg | cut -d - -f 2`
echo "upload : $pkg"
echo "version: $version"

echo twine upload dist/*
#twine upload dist/*

echo git tag -a v$version -m "v$version"
#git tag -a v$version -m "v$version"

echo git push origin --tags
#git push origin --tags
