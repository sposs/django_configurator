# -*- coding: utf-8 -*-
"""
© 2012 - 2016 Xample Sàrl

Author: Stephane Poss
Date: 11.01.17
"""
import os

from django.core.management.base import CommandError
from django.template.context import Context
from django.template.loader import get_template


def handle_pip_config(options, output, test=True):
    """
    Configure pip to use a dedicated pypi server
    :param dict options:
    :param stream output:
    :param bool test:
    :return: None
    """
    if not options.get("pippass") or not options.get("pipuser"):
        raise CommandError("You must specify the pip pass and user.")
    pip_conf_dir = os.path.join(os.environ["HOME"], ".pip")
    if not os.path.isdir(pip_conf_dir):
        os.makedirs(pip_conf_dir)
    pip_conf = os.path.join(pip_conf_dir, "pip.conf")
    pipconf = {
        "username": options.get("pipuser"),
        "password": options.get("pippass"),
        "host": options.get("piphost"),
        "port": options.get("pipport"),
        "secure": options.get("pipsecure")
    }
    t = get_template("pip.conf")
    c = Context(pipconf)
    pipconf = t.render(c)
    if test:
        output.write(pipconf)
    else:
        try:
            with open(pip_conf, "w") as conf:
                conf.write(pipconf)
        except OSError:
            raise CommandError("Cannot modify the pip.conf, make sure you have the proper rights.")
