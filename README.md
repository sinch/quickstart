# Bootstrap Script for Sinch iOS SDK Quickstart 

_quickstart.py_ is a script that is used to download and setup sample projects 
for the Sinch iOS SDK as part of the Quickstart / Tutorial on www.sinch.com. 

The quickstart is presented the first time you create a Developer account on www.sinch.com, 
and guides the developer in setting up sample apps for _App-to-App Calling_,
_App-to-Phone Calling_, and _Instant Messaging_ with the Sinch iOS SDK.

The script will:

- Download the latest Sinch iOS SDK (to a temporary folder)
- Provision the sample project with your Sinch application credentials
- Move the unpacked Sinch SDK including samples to ~/Desktop/Sinch-\<sample name\>
- Launch Xcode and open the Sinch sample


# Development

The script should be validated with pylint (http://www.pylint.org/)

A useful tool to apply automatable fixes for pep8 conformance is autopep8 (https://pypi.python.org/pypi/autopep8)

# Testing manually

    cat testdata/testdata.json | base64 | xargs -J{} ./quickstart.py {}
    
# Automated testing across multiple Python versions

This bootstrap script must be tested on multiple python versions.
We use _pyenv_ (https://github.com/yyuu/pyenv) to manage multiple python versions.

## Install pyenv via homebrew

    $ brew update
    $ brew install pyenv
    
## Run tests (across multiple Python versions)

    ./test.sh

This will install quite a few versions of python (placed in ~/.pyenv/versions) so first run may take a while.
