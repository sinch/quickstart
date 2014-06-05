#!/usr/bin/env bash

# init pyenv (will add pyenv shims to your $PATH)
if which pyenv > /dev/null; 
  then eval "$(pyenv init -)"; 
else
  echo "pyenv not found. Exiting..." && exit 1
fi

declare -a pyversions
pyversions=("2.6.6" "2.7.2" "2.7.3" "2.7.5" "2.7.6" "3.2.5" "3.3.5" "3.4.0")

# install python versions via pyenv
echo "Installing necessary Python versions"
for pyv in "${pyversions[@]}"; do
  pyenv versions | grep $pyv > /dev/null
  if [ $? -eq 0 ]; then
    echo "python $pyv already installed, skipping..."
  else
    echo "installing python $pyv via pyenv..."
    pyenv install $pyv
  fi
done

pyenv rehash

# run quickstart.py with input from testdata.json file.

function cleanup() {
  # pyenv will create a .python-version, remove it
  rm -rf .python-version
}

test_input_files=('testdata/testdata-optionals.json' 'testdata/testdata.json')

for pyv in "${pyversions[@]}"; do
  pyenv local $pyv # set current local version
  echo "Testing with Python version:"
  pyenv exec python "--version"
  for input_file in "${test_input_files[@]}"; do
      echo "Testing with input data from $input_file"
      pyenv exec python "-u" "./quickstart.py" $(cat $input_file | base64)
      if [ $? -ne 0 ]; then
          echo "FAIL" && cleanup && exit 1
      fi
  done
done

cleanup

