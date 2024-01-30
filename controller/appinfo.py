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

    def get(self):
        return json.loads(json.dumps(self.info))
