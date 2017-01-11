# -*- coding: utf-8 -*-
"""
© 2012 - 2016 Xample Sàrl

Author: Stephane Poss
Date: 11.01.17
"""
import os
import subprocess
import tempfile

from django.core.management.base import CommandError
from django.template.context import Context
from django.template.loader import get_template

SERVER_CONFIG = {"apache": "/etc/apache2/sites-enabled/"}


def get_server_install_cmd(server_type):
    """
    Depending on the platform, we want to install some modules for the server
    :param str server_type: a server type, e.g. apache or nginx
    :return: str
    """
    if server_type == "apache":
        return "apt-get install apache2 libapache2-mod-wsgi -y"
    elif server_type == "django":
        return None  # nothing special to do for django runserver
    elif server_type is None:
        return None
    else:
        raise NotImplementedError("%s installation not defined" % server_type)


def handle_server_config(server_type, project_name, project_path):
    """
    determine the server config files and the path where to store the resulting file
    :param server_type:
    :param project_name:
    :param project_path:
    :return:
    """
    if server_type == "apache":
        return "apache_conf.conf", {"project": project_name,
                                    "staticdir": None,
                                    "servername": None,
                                    "servermail": None,
                                    "wsgipath": None}
    elif server_type == "django":
        return None, None
    elif server_type is None:
        return None, None
    else:
        raise NotImplementedError("%s server config is missing" % server_type)


def install_server(server_type, project_name, project_path, output, test=True):
    """
    install and configure the server
    :param server_type:
    :param project_name:
    :param project_path:
    :param output:
    :param test:
    :return:
    """
    if not server_type:
        return True
    output.write(">> Installing the server")
    install_cmd = get_server_install_cmd(server_type)
    if not test:
        o = ""
        try:
            o = subprocess.check_output(install_cmd)
        except subprocess.CalledProcessError as err:
            output.write(err.output)
            raise CommandError("Failed the server package installation")
        finally:
            output.write(o)
    else:
        output.write(install_cmd)

    # now define the config file for the server
    try:
        t_name, t_dict = handle_server_config(server_type, project_name, project_path)
    except Exception as err:
        raise CommandError(str(err))
    if t_name:
        t = get_template(t_name)
        c = Context(t_dict)
        server_config = t.render(c)
        if test:
            output.write(server_config)
        else:
            path = SERVER_CONFIG.get(server_type)
            try:
                with open(os.path.join(path, project_name + ".conf"), "w") as s_cnf:
                    s_cnf.write(server_config)
            except OSError:
                raise CommandError("Could not save the server config file in its final location")
    return True
