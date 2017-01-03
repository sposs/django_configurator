#  -*- coding: utf-8 -*-
"""
Copyright 2016 S. Poss
"""
import subprocess
import tempfile

from django.core.management.base import BaseCommand, CommandError
import random
import os

from django.template.context import Context
from django.template.loader import get_template

__author__ = 'sposs'


class Command(BaseCommand):
    base_path = "/opt"
    virtual_envs_path = "/opt/virtualenvs"
    secret_key = ''.join(
        [random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789'
                                      '!@#$%^&*(-_=+)') for _ in range(50)])

    def add_arguments(self, parser):
        parser.add_argument("project", help="project name")
        parser.add_argument("-p", "--path", dest="base_path",
                            help="The root path", default=self.base_path)
        parser.add_argument("-v", "--virtualenv", dest="virtenv",
                            help="The path to the virtualenvs root",
                            default=self.virtual_envs_path)
        parser.add_argument("--pippass", help="the pip password", dest="pippass")
        parser.add_argument("--pipuser", help="the pip username", dest="pipuser")
        parser.add_argument("--piphost", help="the pip server", dest="piphost")
        parser.add_argument("--pipport", help="the pip port", dest="pipport")
        parser.add_argument("--pipsecure", help="the pip server uses https", dest="pipsecure", action="store_true")

    def handle(self, *args, **options):
        y = raw_input("Continue? [y,n] > ")
        if y.lower() not in ["y", "yes"]:
            raise CommandError("Canceled before ending.")
        #  handle the pip config file
        if "HOME" in os.environ and options.get("piphost"):
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
            with open(pip_conf, "w") as conf:
                conf.write(pipconf)
        else:
            self.stderr.write("The HOME directory is not defined, cannot overwrite the pip config file")
        if "WORKON_HOME" not in os.environ:
            workonhome = options.get("virtenv")
        else:
            workonhome = os.environ.get("WORKON_HOME")

        setup_params = {
            "workonhome": workonhome,
            "project": options.get("project")
        }
        t = get_template("setup.sh")
        c = Context(setup_params)
        setup_script = t.render(c)
        tmpf = tempfile.mktemp()
        with open(tmpf, "w") as script:
            script.write(setup_script)
        os.chmod(tmpf, 0755)
        output = ""
        try:
            output = subprocess.check_output(tmpf)
        except subprocess.CalledProcessError:
            self.stderr.write(output)
            raise CommandError("Failed to install the script")
        #  locate virtual env by inspecting os.environ
        #  create virtualenv
        #  configure pip source (.pip/pip.conf)
        #  install package using pip
        #  deploy config file
        #  deploy apache file
        #  email config
        #  DB config
