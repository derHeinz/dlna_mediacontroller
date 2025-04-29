#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import datetime


class AppInfo(object):

    def __init__(self):
        self.info = {}
        self._collect()

    def _collect(self):
        """collect some base information"""
        self.info['inittime'] = datetime.datetime.now().isoformat()
        self.info['pid'] = str(os.getpid())

    def register(self, key, value):
        """register additional information"""
        self.info[key] = value

    def _to_value(self, value):
        if callable(value):
            return value()
        return value

    def get(self):
        res = {k: self._to_value(v) for k, v in self.info.items()}
        return json.loads(json.dumps(res))
