
rm -rf build dist

python3 setup.py bdist_wheel

pkg=`find dist -type f -name "*-py3-*.whl" -print -quit`

pip3 uninstall -y pygpsd

if [[ "$VIRTUAL_ENV" != "" || "$EUID" -eq 0 ]]
then
    pip3 install $pkg
else
    pip3 install --user $pkg
fi
