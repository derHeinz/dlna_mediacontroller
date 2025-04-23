#!/usr/bin/python3
# -*- coding: utf

import unittest
from controller.appinfo import AppInfo


class TestAppInfo(unittest.TestCase):

    def _create_testee(self) -> AppInfo:
        return AppInfo()

    def test_get(self):
        default_result = self._create_testee().get()
        self.assertTrue(default_result.get('inittime'))
        self.assertEqual('foo'.upper(), 'FOO')

    def test_register(self):
        t = self._create_testee()
        bla = {"foo": "bar"}
        t.register("bla", bla)
        res = t.get()

        self.assertEqual(bla, res.get('bla'))
