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

    def test_register_func(self):
        t = self._create_testee()

        def yield_number():
            return 42
        
        t.register('foo', yield_number)

        res = t.get()
        self.assertEqual(42, res.get('foo'))

    def bla(self):
        return 42

    def test_register_func_self(self):
        t = self._create_testee()

        t.register('foo', self.bla)

        res = t.get()
        self.assertEqual(42, res.get('foo'))
