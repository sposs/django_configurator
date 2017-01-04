#  -*- coding: utf-8 -*-
"""
Copyright 2016 S. Poss
"""
import subprocess
import tempfile
import pkg_resources
from django.core.management.base import BaseCommand, CommandError
import random
import os

from django.template.context import Context
from django.template.loader import get_template

from configurator.utils import get_server_install_cmd, handle_server_config

__author__ = 'sposs'


SERVER_CONFIG = {"apache": "/etc/apache2/sites-enabled/"}

class Command(BaseCommand):
    base_path = "/opt"
    virtual_envs_path = "/opt/virtualenvs"
    secret_key = ''.join(
        [random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789'
                                      '!@#$%^&*(-_=+)') for _ in range(50)])
    test = False

    def add_arguments(self, parser):
        parser.add_argument("project", help="project name")
        parser.add_argument("-p", "--path", dest="base_path",
                            help="The root path", default=self.base_path)
        parser.add_argument("-e", "--virtualenv", dest="virtenv",
                            help="The path to the virtualenvs root",
                            default=self.virtual_envs_path)
        parser.add_argument("--pippass", help="the pip password", dest="pippass")
        parser.add_argument("--pipuser", help="the pip username", dest="pipuser")
        parser.add_argument("--piphost", help="the pip server", dest="piphost")
        parser.add_argument("--pipport", help="the pip port", dest="pipport")
        parser.add_argument("--pipsecure", help="the pip server uses https", dest="pipsecure", action="store_true")
        parser.add_argument("--dev", dest="test", action="store_true", help="Do not run anything, "
                                                                            "only dump the templates")
        parser.add_argument("-s", "--server", dest="server", choices=["apache", "nginx", "django"])
        parser.add_argument("--update", dest="update", help="run the update of the project?", action="store_true")

    def handle(self, *args, **options):
        # y = raw_input("Continue? [y,n] > ")
        # if y.lower() not in ["y", "yes"]:
        #     raise CommandError("Canceled before ending.")

        self.virtual_envs_path = options.get("virtenv")
        self.test = options.get("test", False)
        #  handle the pip config file
        if "HOME" in os.environ:
            if options.get("piphost"):
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
                if self.test:
                    self.stdout.write(pipconf)
                else:
                    try:
                        with open(pip_conf, "w") as conf:
                            conf.write(pipconf)
                    except OSError:
                        raise CommandError("Cannot modify the pip.conf, make sure you have the proper rights.")
        else:
            self.stderr.write("The HOME directory is not defined, cannot overwrite the pip config file")
        try:
            os.makedirs(os.path.join(self.virtual_envs_path, "test233421"))
        except OSError:
            raise CommandError("Write access forbidden in %s" % self.virtual_envs_path)
        else:
            os.rmdir(os.path.join(self.virtual_envs_path, "test233421"))
        _requirement = pkg_resources.Requirement.parse(options.get("project"))
        project_name = _requirement.project_name
        project_path = os.path.join(self.virtual_envs_path, project_name)
        virtenv_dir_exists = os.path.isdir(self.virtual_envs_path)
        server_type = options.get("server")

        server_install_cmd = get_server_install_cmd(server_type)
        setup_params = {
            "virtenv_exists": virtenv_dir_exists,
            "workonhome": self.virtual_envs_path,
            "make_env_dir": not os.path.isdir(project_path),
            "project": project_name,
            "server_install_cmd": server_install_cmd,
            "update": options.get("update"),
            "requirement": str(_requirement)
        }
        t = get_template("setup.sh")
        c = Context(setup_params)
        setup_script = t.render(c)
        if self.test:
            self.stdout.write(setup_script)
        else:
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
            finally:
                os.unlink(tmpf)

        try:
            t_name, t_dict = handle_server_config(server_type, project_name, project_path)
        except Exception as err:
            raise CommandError(err)
        if t_name:
            t = get_template(t_name)
            c = Context(t_dict)
            server_config = t.render(c)
            if self.test:
                self.stdout.write(server_config)
            else:
                path = SERVER_CONFIG.get(server_type)
                with open(os.path.join(path, project_name+".conf"), "w") as s_cnf:
                    s_cnf.write(server_config)
        #  locate virtual env by inspecting os.environ
        #  create virtualenv
        #  configure pip source (.pip/pip.conf)
        #  install package using pip
        #  deploy config file
        #  deploy apache file
        #  email config
        #  DB config
