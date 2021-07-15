#!usr/bin/bash

pip uninstall googletrans
git clone https://github.com/BoseCorp/py-googletrans.git
cd ./py-googletrans
python setup.py install
cd ..
rm -r py-googletrans
