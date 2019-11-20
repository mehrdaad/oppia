# coding: utf-8
#
# Copyright 2019 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for scripts/setup.py."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import collections
import os
import platform
import subprocess
import sys
import tarfile

from core.tests import test_utils

import python_utils

from . import clean
from . import common
from . import setup

RELEASE_TEST_DIR = os.path.join('core', 'tests', 'release_sources', '')
MOCK_TMP_UNTAR_PATH = os.path.join(RELEASE_TEST_DIR, 'tmp_unzip.tar.gz')
NODE_VERSION = setup.NODE_VERSION
YARN_VERSION = setup.YARN_VERSION


class SetupTests(test_utils.GenericTestBase):
    """Test the methods for setup script."""

    def setUp(self):
        super(SetupTests, self).setUp()
        self.check_function_calls = {
            'create_directory_is_called': False,
            'test_python_version_is_called': False,
            'recursive_chown_is_called': False,
            'recursive_chmod_is_called': False,
            'rename_is_called': False,
            'delete_file_is_called': False
        }
        self.urls = []
        def mock_create_directory(unused_path):
            self.check_function_calls['create_directory_is_called'] = True
        def mock_test_python_version():
            self.check_function_calls['test_python_version_is_called'] = True
        def mock_download_and_install_package(url, unused_filename):
            self.urls.append(url)
        def mock_exists(unused_path):
            return True
        def mock_recursive_chown(unused_path, unused_uid, unused_gid):
            self.check_function_calls['recursive_chown_is_called'] = True
        def mock_recursive_chmod(unused_path, unused_mode):
            self.check_function_calls['recursive_chmod_is_called'] = True
        def mock_uname():
            return ['Linux']
        def mock_rename(unused_path1, unused_path2):
            self.check_function_calls['rename_is_called'] = True
        def mock_isfile(unused_path):
            return True
        def mock_delete_file(unused_path):
            self.check_function_calls['delete_file_is_called'] = True
        def mock_get(unused_var):
            return None

        self.create_swap = self.swap(
            setup, 'create_directory', mock_create_directory)
        self.test_py_swap = self.swap(
            setup, 'test_python_version', mock_test_python_version)
        self.download_swap = self.swap(
            setup, 'download_and_install_package',
            mock_download_and_install_package)
        self.exists_swap = self.swap(os.path, 'exists', mock_exists)
        self.chown_swap = self.swap(
            common, 'recursive_chown', mock_recursive_chown)
        self.chmod_swap = self.swap(
            common, 'recursive_chmod', mock_recursive_chmod)
        self.uname_swap = self.swap(platform, 'uname', mock_uname)
        self.rename_swap = self.swap(os, 'rename', mock_rename)
        self.isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        self.delete_swap = self.swap(clean, 'delete_file', mock_delete_file)
        self.get_swap = self.swap(os.environ, 'get', mock_get)

    def test_create_directory_tree_with_missing_dir(self):
        check_function_calls = {
            'makedirs_is_called': False
        }
        def mock_makedirs(unused_path):
            check_function_calls['makedirs_is_called'] = True
        def mock_exists(unused_path):
            return False
        makedirs_swap = self.swap(os, 'makedirs', mock_makedirs)
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        with makedirs_swap, exists_swap:
            setup.create_directory('dir')
        self.assertTrue(check_function_calls['makedirs_is_called'])

    def test_create_directory_tree_with_existing_dir(self):
        check_function_calls = {
            'makedirs_is_called': False
        }
        def mock_makedirs(unused_path):
            check_function_calls['makedirs_is_called'] = True
        def mock_exists(unused_path):
            return True
        makedirs_swap = self.swap(os, 'makedirs', mock_makedirs)
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        with makedirs_swap, exists_swap:
            setup.create_directory('dir')
        self.assertFalse(check_function_calls['makedirs_is_called'])

    def test_python_version_testing_with_correct_version(self):
        version_info = collections.namedtuple(
            'version_info', ['major', 'minor'])
        with self.swap(
            sys, 'version_info', version_info(major=2, minor=7)):
            setup.test_python_version()

    def test_python_version_testing_with_incorrect_version_and_linux_os(self):
        print_arr = []
        def mock_print(msg_list):
            print_arr.extend(msg_list)
        print_swap = self.swap(
            common, 'print_each_string_after_two_new_lines', mock_print)
        os_swap = self.swap(common, 'OS_NAME', 'Linux')
        version_info = collections.namedtuple(
            'version_info', ['major', 'minor'])
        version_swap = self.swap(
            sys, 'version_info', version_info(major=3, minor=4))
        with print_swap, os_swap, version_swap, self.assertRaises(Exception):
            setup.test_python_version()
        self.assertEqual(print_arr, [])

    def test_python_version_testing_with_incorrect_version_and_windows_os(self):
        print_arr = []
        def mock_print(msg_list):
            print_arr.extend(msg_list)

        print_swap = self.swap(
            common, 'print_each_string_after_two_new_lines', mock_print)
        uname_swap = self.swap(common, 'OS_NAME', 'Windows')
        version_info = collections.namedtuple(
            'version_info', ['major', 'minor'])
        version_swap = self.swap(
            sys, 'version_info', version_info(major=3, minor=4))
        with print_swap, uname_swap, version_swap, self.assertRaises(Exception):
            setup.test_python_version()
        self.assertEqual(
            print_arr, [
                'It looks like you are using Windows. If you have Python '
                'installed,',
                'make sure it is in your PATH and that PYTHONPATH is set.',
                'If you have two versions of Python (ie, Python 2.7 and 3), '
                'specify 2.7 before other versions of Python when setting the '
                'PATH.',
                'Here are some helpful articles:',
                'http://docs.python-guide.org/en/latest/starting/install/win/',
                'https://stackoverflow.com/questions/3701646/how-to-add-to-the-'
                'pythonpath-in-windows-7'])

    def test_download_and_install_package(self):
        check_function_calls = {
            'url_retrieve_is_called': False,
            'open_is_called': False,
            'extractall_is_called': False,
            'close_is_called': False,
            'remove_is_called': False
        }
        expected_check_function_calls = {
            'url_retrieve_is_called': True,
            'open_is_called': True,
            'extractall_is_called': True,
            'close_is_called': True,
            'remove_is_called': True
        }
        # pylint: disable=unused-argument
        def mock_url_retrieve(unused_url, filename):
            check_function_calls['url_retrieve_is_called'] = True
        temp_file = tarfile.open(name=MOCK_TMP_UNTAR_PATH)
        def mock_open(name):
            check_function_calls['open_is_called'] = True
            return temp_file
        def mock_extractall(unused_self, path):
            check_function_calls['extractall_is_called'] = True
        # pylint: enable=unused-argument
        def mock_close(unused_self):
            check_function_calls['close_is_called'] = True
        def mock_remove(unused_path):
            check_function_calls['remove_is_called'] = True

        url_retrieve_swap = self.swap(
            python_utils, 'url_retrieve', mock_url_retrieve)
        open_swap = self.swap(tarfile, 'open', mock_open)
        extract_swap = self.swap(tarfile.TarFile, 'extractall', mock_extractall)
        close_swap = self.swap(tarfile.TarFile, 'close', mock_close)
        remove_swap = self.swap(os, 'remove', mock_remove)

        with url_retrieve_swap, open_swap, extract_swap, close_swap:
            with remove_swap, self.uname_swap:
                setup.download_and_install_package('url', 'filename.tgz')
        self.assertEqual(check_function_calls, expected_check_function_calls)

    def test_download_and_install_package_on_windows(self):
        check_function_calls = {
            'url_retrieve_is_called': False,
            'popen_is_called': False,
            'communicate_is_called': False,
            'remove_is_called': False
        }
        expected_check_function_calls = {
            'url_retrieve_is_called': True,
            'popen_is_called': True,
            'communicate_is_called': True,
            'remove_is_called': True
        }
        # pylint: disable=unused-argument
        def mock_url_retrieve(unused_url, filename):
            check_function_calls['url_retrieve_is_called'] = True
        temp_popen = subprocess.Popen(
            ['python', '--version'], stdout=sys.stdout)
        def mock_popen(command, stdout):
            check_function_calls['popen_is_called'] = True
            return temp_popen
        def mock_communicate(p):
            check_function_calls['communicate_is_called'] = True
        # pylint: enable=unused-argument
        def mock_remove(unused_path):
            check_function_calls['remove_is_called'] = True
        os_mock = self.swap(common, 'OS_NAME', 'Windows')

        url_retrieve_swap = self.swap(
            python_utils, 'url_retrieve', mock_url_retrieve)
        popen_swap = self.swap(subprocess, 'Popen', mock_popen)
        communicate_swap = self.swap(
            subprocess.Popen, 'communicate', mock_communicate)
        remove_swap = self.swap(os, 'remove', mock_remove)

        with url_retrieve_swap, popen_swap, communicate_swap:
            with remove_swap, os_mock:
                setup.download_and_install_package('url', 'filename.zip')
        self.assertEqual(check_function_calls, expected_check_function_calls)

    def test_invalid_dir(self):
        def mock_getcwd():
            return 'invalid'
        print_arr = []
        def mock_print(msg):
            print_arr.append(msg)

        getcwd_swap = self.swap(os, 'getcwd', mock_getcwd)
        print_swap = self.swap(python_utils, 'PRINT', mock_print)
        with self.test_py_swap, getcwd_swap, print_swap, self.assertRaises(
            Exception):
            setup.main(args=[])
        self.assertTrue(
            'WARNING   This script should be run from the oppia/ '
            'root folder.' in print_arr)
        self.assertTrue(
            self.check_function_calls['test_python_version_is_called'])

    def test_package_install_with_darwin_x64(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 1000
        os_swap = self.swap(common, 'OS_NAME', 'Darwin')
        architect_swap = self.swap(common, 'ARCHITECTURE', 'x86_64')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)

        with self.test_py_swap, self.create_swap:
            with os_swap, exists_swap, getuid_swap, architect_swap:
                with self.download_swap, self.rename_swap, self.chown_swap:
                    with self.chmod_swap, self.delete_swap, self.isfile_swap:
                        setup.main(args=[])
        for _, item in self.check_function_calls.items():
            self.assertTrue(item)
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-darwin-x64.tar.gz' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_package_install_with_darwin_x86(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 10000
        os_swap = self.swap(common, 'OS_NAME', 'Darwin')
        architecture_swap = self.swap(common, 'ARCHITECTURE', 'x86')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)
        with self.test_py_swap, self.create_swap, os_swap, exists_swap:
            with architecture_swap, self.download_swap, self.rename_swap:
                with self.chmod_swap, self.delete_swap, self.isfile_swap:
                    with self.chown_swap, getuid_swap:
                        setup.main(args=[])
        for _, item in self.check_function_calls.items():
            self.assertTrue(item)
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-darwin-x86.tar.gz' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_package_install_with_linux_x64(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 10000
        os_swap = self.swap(common, 'OS_NAME', 'Linux')
        architecture_swap = self.swap(common, 'ARCHITECTURE', 'x86_64')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)

        with self.test_py_swap, self.create_swap, exists_swap:
            with self.download_swap, self.rename_swap, self.chown_swap:
                with self.chmod_swap, self.delete_swap, self.isfile_swap:
                    with os_swap, getuid_swap, architecture_swap:
                        setup.main(args=[])
        for _, item in self.check_function_calls.items():
            self.assertTrue(item)
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-linux-x64.tar.gz' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_package_install_with_linux_x86(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 10000
        os_swap = self.swap(common, 'OS_NAME', 'Linux')
        architecture_swap = self.swap(common, 'ARCHITECTURE', 'x86')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)

        with self.test_py_swap, self.create_swap, exists_swap:
            with self.download_swap, self.rename_swap, self.chown_swap:
                with self.chmod_swap, self.delete_swap, self.isfile_swap:
                    with os_swap, getuid_swap, architecture_swap:
                        setup.main(args=[])
        for _, item in self.check_function_calls.items():
            self.assertTrue(item)
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-linux-x86.tar.gz' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_package_install_with_windows_x64(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 10000

        check_function_calls = [
            'create_directory_is_called',
            'test_python_version_is_called',
            'rename_is_called',
            'delete_file_is_called'
        ]
        os_swap = self.swap(common, 'OS_NAME', 'Windows')
        architecture_swap = self.swap(common, 'ARCHITECTURE', 'AMD64')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)

        with self.test_py_swap, self.create_swap, exists_swap:
            with self.download_swap, self.rename_swap:
                with self.delete_swap, self.isfile_swap:
                    with os_swap, getuid_swap, architecture_swap:
                        setup.main(args=[])
        for item in check_function_calls:
            self.assertTrue(self.check_function_calls[item])
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-win-x64.zip' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_package_install_with_windows_x86(self):
        def mock_exists(unused_path):
            return False
        def mock_getuid():
            return 10000

        check_function_calls = [
            'create_directory_is_called',
            'test_python_version_is_called',
            'rename_is_called',
            'delete_file_is_called'
        ]
        os_swap = self.swap(common, 'OS_NAME', 'Windows')
        architecture_swap = self.swap(common, 'ARCHITECTURE', 'AMD86')
        exists_swap = self.swap(os.path, 'exists', mock_exists)
        getuid_swap = self.swap(os, 'getuid', mock_getuid)

        with self.test_py_swap, self.create_swap, exists_swap:
            with self.download_swap, self.rename_swap:
                with self.delete_swap, self.isfile_swap:
                    with os_swap, getuid_swap, architecture_swap:
                        setup.main(args=[])
        for item in check_function_calls:
            self.assertTrue(self.check_function_calls[item])
        self.assertEqual(
            self.urls, [
                'https://nodejs.org/dist/%s/node-%s'
                '-win-x86.zip' % (NODE_VERSION, NODE_VERSION),
                'https://github.com/yarnpkg/yarn/releases/download/'
                '%s/yarn-%s.tar.gz' % (YARN_VERSION, YARN_VERSION)])

    def test_chrome_bin_setup_with_travis_var_set(self):
        def mock_get(unused_var):
            return 'Travis'
        get_swap = self.swap(os.environ, 'get', mock_get)

        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap, get_swap:
                setup.main(args=[])
        self.assertEqual(os.environ['CHROME_BIN'], '/usr/bin/chromium-browser')

    def test_chrome_bin_setup_with_google_chrome(self):
        def mock_isfile(path):
            return path == '/usr/bin/google-chrome'
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(os.environ['CHROME_BIN'], '/usr/bin/google-chrome')

    def test_chrome_bin_setup_with_chromium_browser(self):
        def mock_isfile(path):
            return path == '/usr/bin/chromium-browser'
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(os.environ['CHROME_BIN'], '/usr/bin/chromium-browser')

    def test_chrome_bin_setup_with_chrome_exe_c_files(self):
        def mock_isfile(path):
            return (
                path == (
                    '/c/Program Files (x86)/Google/Chrome/'
                    'Application/chrome.exe'))
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(
            os.environ['CHROME_BIN'],
            '/c/Program Files (x86)/Google/Chrome/Application/chrome.exe')

    def test_chrome_bin_setup_with_chrome_exe_mnt_files(self):
        def mock_isfile(path):
            return (
                path == (
                    '/mnt/c/Program Files (x86)/Google/Chrome/'
                    'Application/chrome.exe'))
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(
            os.environ['CHROME_BIN'],
            '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe')

    def test_chrome_bin_setup_with_mac_google_chrome(self):
        def mock_isfile(path):
            return (
                path == (
                    '/Applications/Google Chrome.app/Contents/MacOS/'
                    'Google Chrome'))
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(
            os.environ['CHROME_BIN'],
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

    def test_chrome_bin_setup_with_windows_google_chrome(self):
        def mock_isfile(path):
            return (
                path == (
                    'c:\\Program Files (x86)\\Google\\Chrome\\Application\\'
                    'chrome.exe'))
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap:
                with self.get_swap, isfile_swap:
                    setup.main(args=[])
        self.assertEqual(
            os.environ['CHROME_BIN'],
            'c:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe')

    def test_chrome_bin_setup_with_error(self):
        def mock_isfile(unused_path):
            return False
        print_arr = []
        def mock_print(msg):
            print_arr.append(msg)
        isfile_swap = self.swap(os.path, 'isfile', mock_isfile)
        print_swap = self.swap(python_utils, 'PRINT', mock_print)

        with self.test_py_swap, self.create_swap, self.uname_swap:
            with self.exists_swap, self.chown_swap, self.chmod_swap, print_swap:
                with isfile_swap, self.get_swap, self.assertRaises(Exception):
                    setup.main(args=[])
        self.assertTrue('Chrome is not found, stopping ...' in print_arr)