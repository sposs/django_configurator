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

    def handle(self, *args, **options):
        # y = raw_input("Continue? [y,n] > ")
        # if y.lower() not in ["y", "yes"]:
        #     raise CommandError("Canceled before ending.")

        self.virtual_envs_path = options.get("virtenv")
        self.test = options.get("test", False)

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
        _requirement = pkg_resources.Requirement.parse(options.get("project"))
        project_name = _requirement.project_name
        project_path = os.path.join(self.virtual_envs_path, project_name)
        virtenv_dir_exists = os.path.isdir(self.virtual_envs_path)

        #  handle the DB installation + configuration
        db_type = options.get("dbtype")
        dbname = options.get("dbname")
        db_user = db_pass = None
        if db_type:
            db_user, db_pass = configure_database(db_type, dbname, self.stdout, self.test)

        #  handle the server installation
        server_type = options.get("server")
        if server_type:
            all_ok = install_server(server_type, project_name, project_path, self.stdout, self.test)
            if not all_ok:
                raise CommandError("Failed installing the DB")

        #  the basic script: install packages, configure the virtualenv
        setup_params = {
            "virtenv_exists": virtenv_dir_exists,
            "workonhome": self.virtual_envs_path,
            "make_env_dir": not os.path.isdir(project_path),
            "project": project_name,
            "update": options.get("update"),
            "requirement": str(_requirement)
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
        activate_this = locate_activate_this(project_path)


        #  deploy config file
        #  deploy apache file
        #  email config
        #  DB config
