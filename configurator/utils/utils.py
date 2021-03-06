#  -*- coding: utf-8 -*-
"""
Copyright 2016
"""
import getpass
import json
import os
import tempfile

from django.template.context import Context
from django.template.loader import get_template

from configurator.exceptions import SettingsMissing, ConfigMissing, BadConfig

__author__ = 'sposs'

settings_path = os.environ.get("SECRETS_FILE", "")
dj_secrets = {}


def set_settings(path=None):
    """
    Configure the settings
    :param path: a path to the setting
    :return: None
    """
    global settings_path
    global dj_secrets
    if path:
        settings_path = path
    if not settings_path:
        settings_path = os.path.expanduser("~/settings.json")

    if not os.path.exists(settings_path):
        raise SettingsMissing("Settings file not found at %s!" % settings_path)

    with open(settings_path) as f:
        try:
            dj_secrets = json.loads(f.read())
        except Exception:
            raise SettingsMissing("Settings file is corrupted")


my_config = {}
config_path = os.environ.get("CONFIG_PATH", "")


def set_config(path=None):
    """
    Configure the config.json path
    :param path: the path to the config.json of this project
    :return: None
    """
    global config_path
    global my_config

    if path:
        config_path = path

    if not config_path:
        config_path = os.path.expanduser("~/config.json")

    if not os.path.exists(config_path):
        raise ConfigMissing("Configuration file not found at %s" % config_path)

    with open(config_path) as f:
        try:
            my_config = json.loads(f.read())
        except Exception:
            raise ConfigMissing("Configuration file is corrupted")


def get_config(setting, default=None, config=None, source="local configuration"):
    """
    Get some installation configuration parameters
    :param string setting: the setting key one wants to access
    :param object default: a default value in case it's not found
    :param dict config: a config dict
    :param str source: the source of the missing config
    :return: the value for the setting
    """
    global my_config
    if not config:
        config = my_config
    val = config.get(setting, default)
    if val is not None:
        return default
    else:
        error_msg = "Missing key %s in %s." % (setting, source)
        raise BadConfig(error_msg)


def get_secret(setting, default=None, secrets=None):
    """
    Get a secret from the configuration
    :param setting: secret parameter to look up
    :param default: a default value for the parameter
    :param dict secrets: a possible dictionary of secret parameters
    :return: a value for the setting or raise an error
    """
    global dj_secrets
    if secrets is None:
        secrets = dj_secrets
    return get_config(setting, default, secrets, "secrets file")


def locate_activate_this(path):
    """
    Find the activate_this.py, needed
    :param path:
    :return:
    """
    file_to_find = "activate_this.py"
    for element in os.walk(path):
        if file_to_find in element[2]:
            return os.path.join(element[0], file_to_find)


def change_ownership(path, uid, gid):
    """
    We need to be able to change the access rights to some users, for example the www-data in case of apache
    :param path: the path to change
    :param uid:
    :param gid:
    :return:
    """
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for directory in dirs:
            os.chown(os.path.join(root, directory), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)
