#  -*- coding: utf-8 -*-
"""
Copyright 2016 S. Poss
"""
import subprocess
import pexpect
import tempfile
import pkg_resources
from django.core.management.base import BaseCommand, CommandError
import random
import os
import re

from django.template.context import Context
from django.template.loader import get_template
from configurator.utils.database import configure_database
from configurator.utils.pip_config import handle_pip_config
from configurator.utils.server import install_server
from configurator.utils.utils import locate_activate_this

__author__ = 'sposs'


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
        parser.add_argument("-d", "--dbtype", dest="dbtype", choices=["postgres", "mysql", "mongo", "sqlite"])
        parser.add_argument("--dbname", dest="dbname", help="The name of the database")
        parser.add_argument("--update", dest="update", help="run the update of the project?", action="store_true")
        parser.add_argument("--vhost", dest="vhost", help="The virtualhost served", required=True)

    def handle(self, *args, **options):
        # y = raw_input("Continue? [y,n] > ")
        # if y.lower() not in ["y", "yes"]:
        #     raise CommandError("Canceled before ending.")
        self.base_path = options.get("base_path")
        self.virtual_envs_path = options.get("virtenv")
        self.test = options.get("test", False)
        vhost = options.get("vhost")

        project = options.get("project")
        if not re.match(r"^[\w-]+=?=?[0-9.]*$", project):
            raise CommandError("The project to install must not contain spaces nor special chars except =.")

        #  handle the pip config file
        if "HOME" in os.environ:
            if options.get("piphost"):
                handle_pip_config(options, self.stdout, self.test)
        else:
            self.stderr.write("The HOME directory is not defined, cannot overwrite the pip config file")

        #  install base packages
        t = get_template("base.sh")
        _, t_path = tempfile.mkstemp(suffix="base.sh")
        with open(t_path, "w") as f:
            f.write(t.render())
        os.chmod(t_path, 0o0755)
        if not self.test:
            output = ""
            try:
                output = subprocess.check_output(t_path)
            except subprocess.CalledProcessError:
                self.stdout.write(output)
                raise CommandError("Failed the installation of basic packages")
        else:
            self.stdout.write(t.render())
        try:
            os.makedirs(os.path.join(self.virtual_envs_path, "test233421"))
        except OSError:
            raise CommandError("Write access forbidden in %s" % self.virtual_envs_path)
        else:
            os.rmdir(os.path.join(self.virtual_envs_path, "test233421"))

        _requirement = pkg_resources.Requirement.parse(project)
        project_name = _requirement.project_name
        project_install_path = os.path.join(self.virtual_envs_path, project_name)
        virtenv_dir_exists = os.path.isdir(self.virtual_envs_path)
        base_path_config = os.path.join(self.base_path, project_name)

        #  handle the DB installation + configuration
        db_type = options.get("dbtype")
        dbname = options.get("dbname")
        db_user = db_pass = None
        if db_type:
            db_user, db_pass = configure_database(db_type, dbname, self.stdout, self.test)

        #  the basic script: install packages, configure the virtualenv
        setup_params = {
            "virtenv_exists": virtenv_dir_exists,
            "workonhome": self.virtual_envs_path,
            "make_env_dir": not os.path.isdir(project_install_path),
            "project": project_name,
            "update": options.get("update"),
            "requirement": str(_requirement),
            "base_path_config": base_path_config
        }
        t = get_template("setup.sh")
        c = Context(setup_params)
        setup_script = t.render(c)
        if self.test:
            self.stdout.write(setup_script)
        else:
            _, tmpf = tempfile.mkstemp()
            with open(tmpf, "w") as script:
                script.write(setup_script)
            os.chmod(tmpf, 0o0755)
            signal = status = 0
            try:
                child = pexpect.spawn(tmpf)
                child.logfile_read = self.stdout
                child.expect(pexpect.EOF)
                child.close()
                status, signal = child.exitstatus, child.signalstatus
            except Exception as err:
                self.stderr.write(str(err))
                raise CommandError("Failed to execute the install script")
            finally:
                os.unlink(tmpf)
            if status:
                raise CommandError("Failed to execute install script")

        # create
        if not self.test:
            if not os.path.isdir("/logs"):
                os.mkdir("/logs")
                os.chmod("/logs", 0o0755)

        activate_this = locate_activate_this(project_install_path)

        # handle config files
        project_config = {"options": {"BASE_VIRTUALENV_ACTIVATE": activate_this,
                                      "HOST_BASE_DEFAULT": vhost}}
        t = get_template("project.conf")
        c = Context(project_config)
        project_secret = t.render(c)
        if self.test:
            self.stdout.write(project_secret)
        else:
            with open(os.path.join(base_path_config, "config.json"), "w") as cfg:
                cfg.write(project_secret)

        project_secret = {"options": {"SECRET_KEY": self.secret_key,
                                      "DB_USER": db_user,
                                      "DB_PASS": db_pass}}
        t = get_template("project.conf")
        c = Context(project_secret)
        secret_cfg = t.render(c)
        if self.test:
            self.stdout.write(secret_cfg)
        else:
            with open(os.path.join(base_path_config, "settings.json"), "w") as cfg:
                cfg.write(secret_cfg)

        #  handle the server installation/configuration.restart
        server_type = options.get("server")
        if server_type:

            all_ok = install_server(vhost, server_type, project_name, project_install_path, base_path_config,
                                    self.stdout, self.test)
            if not all_ok:
                raise CommandError("Failed installing the DB")
        #  email config
        #  DB config
