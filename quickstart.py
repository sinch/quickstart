#!/usr/bin/env python
"""
Licensed under the MIT Licence, Copyright (c) 2014 Sinch / Rebtel Networks AB

A script that bootstraps a sample project from the Sinch iOS SDK.

It can be used to bootstrap samples for App-to-App Calling,
App-to-Phone Calling, and Instant Messaging.

The script takes as a single argument a Base64-encoded JSON which includes
information about: which sample app to bootstrap, and which application
credentials that should be injected. This input data is generated for
your given Sinch account and application, and is embedded in
copy-pasteable code snippets from your dashboard on www.sinch.com.

This script will:
\n- Download the latest Sinch iOS SDK (to a temporary folder)
\n- Provision the sample project with your Sinch application credentials
\n- Move the unpacked Sinch SDK including samples to ~/Desktop/Sinch-<sample>
\n- Launch Xcode and open the Sinch sample

The structure of the JSON input should be:

{
  "archive": "<url to Sinch SDK downloadable artifact>",
  "sample": "<?>", # must be either 'im', 'app-to-app', 'app-to-phone' or 'video'
  "credentials": {
    "application_key": "<?>",
    "application_secret": "<?>",
    "environment": "<?>",
  }
}

Example:

{
  "archive": "http://download.sinch.com/ios/3.0/Sinch-iOS-3.0.0-2cc8ef8.tar.bz2",
  "sample": "im",
  "credentials": {
    "application_key": "bd8dbc2d-053e-44c4-a7da-47d85e2bae59",
    "application_secret": "YmY3ZTU0ZGEtZmEzOC00MA==",
    "environment": "sandbox.sinch.com"
  }
}

The key "archive" is optional, and will default to 'http://www.sinch.com/ios-sdk'
The key "environment" is optional, and will default to 'sandbox.sinch.com'

Usage: quickstart.py Base64(JSON-data)

"""

import os
import sys
import platform
import base64
import json
import re
import tempfile
import shutil
import tarfile
import subprocess

# DEFAULT_ARCHIVE_URL is setup to redirect to the latest Sinch iOS SDK
DEFAULT_ARCHIVE_URL = 'http://www.sinch.com/ios-sdk'
DEFAULT_SINCH_ENVIRONMENT = 'sandbox.sinch.com'


def log(message):
    print ("[INFO] " + message)


class Bootstrap:

    def __init__(self, config):
        self.config = config
        self._path = tempfile.mkdtemp()
        self.archive_path = ""

    def run(self):
        log("Bootstrapping Sinch '%s' sample" % self.sample_name())
        self.archive_path = self.download_archive()
        self.unpack(self.archive_path, self.path())
        self.verify_unpacked()
        self.inject_credentials(self.sample_path())
        self.move_to_desktop()
        self.open_in_finder(self.samples_path())
        self.open_in_xcode(self.xcodeproj_path())

    def path(self, *subpaths):
        return os.path.join(self._path, *subpaths)

    def sample_name(self):
        return self.config['sample']

    def sample_project_name(self):
        samples = {'im': 'SinchIM',
                   'app-to-app': 'SinchCalling',
                   'app-to-phone': 'SinchPSTN',
                   'video': 'SinchVideo'}
        sample = samples.get(self.sample_name())
        if sample is None:
            raise Exception('Could not determine which sample to prepare')
        return sample

    def samples_path(self):
        return self.path('Sinch', 'samples')

    def sample_path(self):
        sample = self.sample_project_name()
        return os.path.join(self.samples_path(), sample)

    def xcodeproj_path(self):
        sample = self.sample_project_name()
        return os.path.join(self.samples_path(), sample + ".xcodeproj")

    def download_archive(self):
        url = self.config['archive']

        try:
            from urllib.request import urlopen  # python 3.x
        except ImportError:
            from urllib2 import urlopen  # python 2.x
        fin = urlopen(url, timeout=30)

        actual_url = fin.geturl()

        # handle if we followed a redirect, e.g.
        # http://www.sinch.com/ios-sdk/ ->
        # http://download.sinch.com/ios/{VERSION}/Sinch-iOS-{VERSION}.tar.bz2
        if actual_url is not None:
            package_name = os.path.basename(actual_url)
            log("Downloading '%s'" % actual_url)
        else:
            package_name = "Sinch.download.tmp"
            log("Downloading '%s'" % url)

        dst = os.path.join(self.path(), package_name)

        with open(dst, 'wb') as fout:
            shutil.copyfileobj(fin, fout)

        if os.stat(dst).st_size <= 0:
            raise Exception("Failed to download '%s' to '%s'" % (url, dst))
        return dst

    def unpack(self, tar_path, dst_dir):
        """Unpack the downloaded Sinch artifiact, i.e. a tar.bz2"""
        log("Extracting '%s'" % os.path.basename(tar_path))
        if not tarfile.is_tarfile(tar_path):
            raise Exception('Unable to read package file %s' % tar_path)
        tar = tarfile.open(tar_path, 'r:bz2')
        tar.extractall(dst_dir)
        return dst_dir

    def verify_unpacked(self):
        sample = self.sample_path()
        if os.path.exists(sample) is not True:
            raise Exception("Could not find sample at path %s" % sample)

    def inject_credentials(self, sample_app_path):
        log("Injecting application credentials in sample source code")
        target_file = os.path.join(sample_app_path, "AppDelegate.m")

        application_key = self.config['credentials.application_key']
        application_secret = self.config['credentials.application_secret']
        environment = self.config['credentials.environment']

        with open(target_file, 'r+') as f:
            source = f.read()
            opts = re.MULTILINE
            source = re.sub(
                r'<APPLICATION KEY>', application_key, source, opts)
            source = re.sub(
                r'<APPLICATION SECRET>', application_secret, source, opts)
            source = re.sub(
                r'\".*\.sinch\.com\"', "\"" + environment + "\"", source, opts)
            f.seek(0)
            f.write(source)
            f.truncate()
            f.flush()

    def get_desktop_candidate(self, basepath):
        assert len(basepath) > 0
        ordinal2suffix = lambda x: '' if x is 0 else '-' + str(x)
        for i in range(99):
            path = basepath + ordinal2suffix(i)
            if not os.path.exists(path):
                return path
        raise Exception(
            'Could not find suitable target directory in ~/Desktop')

    def move_to_desktop(self):
        desktop = os.path.expanduser("~/Desktop")
        if not os.path.exists(desktop):
            raise Exception('Could not locate your Desktop folder')
        basename = "Sinch-" + self.config['sample']
        dst = self.get_desktop_candidate(os.path.join(desktop, basename))
        assert not os.path.exists(dst)
        log("Placing Sinch SDK including sample in '%s'" % dst)
        shutil.copytree(self.path(), dst, symlinks=True)
        self._path = dst
        assert self.path() == dst

    def open_in_finder(self, path):
        _open(path)

    def open_in_xcode(self, path):
        log("Opening Xcode")
        _open(path)


class Config:

    def __init__(self, values, defaults, aliases):
        self.values = values
        self.aliases = aliases
        self.defaults = defaults

    def _get_value(self, values, key, use_alias=True):
        if use_alias and key in self.aliases:
            key = self.aliases[key]
        parts = key.split(".", 1)
        v = values.get(parts[0])
        if v is None:
            return v
        if len(parts) == 1:
            return v
        else:
            return self._get_value(v, parts[1])

    def __getitem__(self, key):
        v = self._get_value(self.values, key)
        if v is None:
            v = self._get_value(self.defaults, key, use_alias=False)
            if v is None:
                raise KeyError("Missing value for key '%s'" % key)
        return v


def read_config(text):
    try:
        try:
            # StringIO.StringIO only exist in Python 2, so we
            # check for that first
            from StringIO import StringIO
            values = json.load(StringIO(base64.b64decode(text)))
        except ImportError:  # python 3
            from io import BytesIO
            from io import TextIOWrapper
            raw = base64.b64decode(bytes(text, 'utf-8'))
            values = json.load(TextIOWrapper(BytesIO(raw), 'utf-8'))

        # the input config may use short keys to minimize the config
        # payload size, so we use key aliases to remap short keys to
        # human readable keys.
        keyaliases = {'archive': 'a',
                      'sample': 's',
                      'credentials.application_key': 'c.k',
                      'credentials.application_secret': 'c.s',
                      'credentials.environment': 'c.e'}

        defaults = {'archive': DEFAULT_ARCHIVE_URL,
                    'credentials': {
                        'environment': DEFAULT_SINCH_ENVIRONMENT
                    }
                    }

        return Config(values, defaults, keyaliases)
    except TypeError as e:
        raise e


def _open(path):
    assert os.path.exists(path)
    subprocess.call(["open", path])


def _which(cmd):
    devnull = open('/dev/null', 'w')
    return subprocess.call("type " + cmd, shell=True, stdout=devnull) == 0


def is_xcode_installed():
    if os.path.exists("/Applications/Xcode.app"):
        return True
    return False


def verify_hostmachine():
    if not platform.system().lower().startswith('darwin'):
        raise Exception('This script is only intended to run on Mac / OS X')
    if not is_xcode_installed():
        raise Exception(
            'Xcode not installed? (Please download Xcode, ' +
            'https://developer.apple.com/xcode/)')


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(
            'Usage: ' + argv[0] + ' <credentials-as-base64ed-json>\n')
        return 1
    try:
        verify_hostmachine()
        config = read_config(argv[1])
        bootstrap = Bootstrap(config)
        return bootstrap.run()
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
