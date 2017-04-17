#!/usr/bin/env python
# coding: utf-8

import mock
from __future__ import unicode_literals, with_statement
import os
import sys
import unittest

from mkdocs import nav, utils, exceptions
from mkdocs.tests.base import dedent
from mock import mock_open, patch

if not utils.PY3:
    import __builtin__ as builtins
else:
    import builtins


class UtilsTests(unittest.TestCase):
    def test_html_path(self):
        expected_results = {
            'index.md': 'index.html',
            'api-guide.md': 'api-guide/index.html',
            'api-guide/index.md': 'api-guide/index.html',
            'api-guide/testing.md': 'api-guide/testing/index.html',
        }
        for file_path, expected_html_path in expected_results.items():
            html_path = utils.get_html_path(file_path)
            self.assertEqual(html_path, expected_html_path)

    def test_url_path(self):
        expected_results = {
            'index.md': '/',
            'api-guide.md': '/api-guide/',
            'api-guide/index.md': '/api-guide/',
            'api-guide/testing.md': '/api-guide/testing/',
        }
        for file_path, expected_html_path in expected_results.items():
            html_path = utils.get_url_path(file_path)
            self.assertEqual(html_path, expected_html_path)

    def test_is_markdown_file(self):
        expected_results = {
            'index.md': True,
            'index.MARKDOWN': True,
            'index.txt': False,
            'indexmd': False
        }
        for path, expected_result in expected_results.items():
            is_markdown = utils.is_markdown_file(path)
            self.assertEqual(is_markdown, expected_result)

    def test_is_html_file(self):
        expected_results = {
            'index.htm': True,
            'index.HTML': True,
            'index.txt': False,
            'indexhtml': False
        }
        for path, expected_result in expected_results.items():
            is_html = utils.is_html_file(path)
            self.assertEqual(is_html, expected_result)

    def test_create_media_urls(self):
        pages = [
            {'Home': 'index.md'},
            {'About': 'about.md'},
            {'Sub': [
                {'Sub Home': 'index.md'},
                {'Sub About': 'about.md'},

            ]}
        ]
        expected_results = {
            'https://media.cdn.org/jq.js': 'https://media.cdn.org/jq.js',
            'http://media.cdn.org/jquery.js': 'http://media.cdn.org/jquery.js',
            '//media.cdn.org/jquery.js': '//media.cdn.org/jquery.js',
            'media.cdn.org/jquery.js': './media.cdn.org/jquery.js',
            'local/file/jquery.js': './local/file/jquery.js',
            'image.png': './image.png',
        }
        site_navigation = nav.SiteNavigation(pages)
        for path, expected_result in expected_results.items():
            urls = utils.create_media_urls(site_navigation, [path])
            self.assertEqual(urls[0], expected_result)

    def test_create_relative_media_url_sub_index(self):
        '''
        test special case where there's a sub/index.md page
        '''

        site_navigation = nav.SiteNavigation([
            {'Home': 'index.md'},
            {'Sub': [
                {'Sub Home': '/subpage/index.md'},

            ]}
        ])
        site_navigation.url_context.set_current_url('/subpage/')
        site_navigation.file_context.current_file = "subpage/index.md"

        def assertPathGenerated(declared, expected):
            url = utils.create_relative_media_url(site_navigation, declared)
            self.assertEqual(url, expected)

        assertPathGenerated("img.png", "./img.png")
        assertPathGenerated("./img.png", "./img.png")
        assertPathGenerated("/img.png", "../img.png")
        assertPathGenerated("https://www.example.com/img.png", "https://www.example.com/img.png")

    def test_reduce_list(self):
        self.assertEqual(
            utils.reduce_list([1, 2, 3, 4, 5, 5, 2, 4, 6, 7, 8]),
            [1, 2, 3, 4, 5, 6, 7, 8]
        )

    def test_get_themes(self):

        self.assertEqual(
            sorted(utils.get_theme_names()),
            ['mkdocs', 'readthedocs'])

    @mock.patch('pkg_resources.iter_entry_points', autospec=True)
    def test_get_theme_dir(self, mock_iter):

        path = 'some/path'

        theme = mock.Mock()
        theme.name = 'mkdocs2'
        theme.dist.key = 'mkdocs2'
        theme.load().__file__ = os.path.join(path, '__init__.py')

        mock_iter.return_value = iter([theme])

        self.assertEqual(utils.get_theme_dir(theme.name), os.path.abspath(path))

    def test_get_theme_dir_keyerror(self):

        self.assertRaises(KeyError, utils.get_theme_dir, 'nonexistanttheme')

    @mock.patch('pkg_resources.iter_entry_points', autospec=True)
    def test_get_theme_dir_importerror(self, mock_iter):

        theme = mock.Mock()
        theme.name = 'mkdocs2'
        theme.dist.key = 'mkdocs2'
        theme.load.side_effect = ImportError()

        mock_iter.return_value = iter([theme])

        self.assertRaises(ImportError, utils.get_theme_dir, theme.name)

    @mock.patch('pkg_resources.iter_entry_points', autospec=True)
    def test_get_themes_warning(self, mock_iter):

        theme1 = mock.Mock()
        theme1.name = 'mkdocs2'
        theme1.dist.key = 'mkdocs2'
        theme1.load().__file__ = "some/path1"

        theme2 = mock.Mock()
        theme2.name = 'mkdocs2'
        theme2.dist.key = 'mkdocs3'
        theme2.load().__file__ = "some/path2"

        mock_iter.return_value = iter([theme1, theme2])

        self.assertEqual(
            sorted(utils.get_theme_names()),
            sorted(['mkdocs2', ]))

    @mock.patch('pkg_resources.iter_entry_points', autospec=True)
    @mock.patch('pkg_resources.get_entry_map', autospec=True)
    def test_get_themes_error(self, mock_get, mock_iter):

        theme1 = mock.Mock()
        theme1.name = 'mkdocs'
        theme1.dist.key = 'mkdocs'
        theme1.load().__file__ = "some/path1"

        theme2 = mock.Mock()
        theme2.name = 'mkdocs'
        theme2.dist.key = 'mkdocs2'
        theme2.load().__file__ = "some/path2"

        mock_iter.return_value = iter([theme1, theme2])
        mock_get.return_value = {'mkdocs': theme1, }

        self.assertRaises(exceptions.ConfigurationError, utils.get_theme_names)

    def test_nest_paths(self):

        j = os.path.join

        result = utils.nest_paths([
            'index.md',
            j('user-guide', 'configuration.md'),
            j('user-guide', 'styling-your-docs.md'),
            j('user-guide', 'writing-your-docs.md'),
            j('about', 'contributing.md'),
            j('about', 'license.md'),
            j('about', 'release-notes.md'),
        ])

        self.assertEqual(
            result,
            [
                'index.md',
                {'User guide': [
                    j('user-guide', 'configuration.md'),
                    j('user-guide', 'styling-your-docs.md'),
                    j('user-guide', 'writing-your-docs.md')]},
                {'About': [
                    j('about', 'contributing.md'),
                    j('about', 'license.md'),
                    j('about', 'release-notes.md')]}
            ]
        )

    def test_unicode_yaml(self):

        yaml_src = dedent(
            '''
            key: value
            key2:
              - value
            '''
        )

        config = utils.yaml_load(yaml_src)
        self.assertTrue(isinstance(config['key'], utils.text_type))
        self.assertTrue(isinstance(config['key2'][0], utils.text_type))

    def test_clean_directory_noop(self):
        deleted = []
        with patch('mkdocs.utils.os.unlink', lambda x: deleted.append(x)):
            # Test the noop
            with patch('mkdocs.utils.os.path.exists', lambda x: False):
                # /etc should always exist on every 'nix system and should
                # be owned by root. Tests should run as non-root and this
                # ensures OSError if the mock isn't working properly
                self.assertIsNone(utils.clean_directory('/etc'))
                self.assertEqual(deleted, [])

    def test_clean_directory(self):
        deleted = []
        directory = '/BOGUSPATH'
        directory_contents = ['README.md', '.sekret_password_file', 'old_crappy_file']
        expected = [os.path.join(directory, i) for i in directory_contents if not i.startswith('.')]

        with patch('mkdocs.utils.os.unlink', lambda x: deleted.append(x)):
            with patch('mkdocs.utils.os.path.exists', lambda x: True):
                with patch('mkdocs.utils.os.listdir', lambda x: directory_contents):
                    utils.clean_directory(directory)
                    self.assertEqual(sorted(deleted), sorted(expected))

    def test_write_file(self):
        new_dirs = []
        filename = '/WATWATWAT/bogus.txt'
        with patch('mkdocs.utils.os.makedirs', lambda x: new_dirs.append(x)):
            with patch.object(builtins, 'open', mock_open(read_data='WAT\n')):
                utils.write_file('WAT\n', filename)
                self.assertEqual(new_dirs, [os.path.dirname(filename)])
