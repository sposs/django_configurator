# -*- coding: utf-8 -*-
"""
© 2012 - 2016 Xample Sàrl

Author: Stephane Poss
Date: 11.01.17
"""
import getpass
import os
import subprocess
import tempfile

import pexpect
from django.core.management.base import CommandError
from django.template.context import Context
from django.template.loader import get_template


def get_db_install_cmd(db_type):
    """
    Depending on the platform, we want to install some modules for the database
    :param str db_type: a database type, e.g. postgres, mongodb, mysql, sqlite
    :return:
    """
    if db_type == "postgres":
        return "apt-get install postgresql libpq-dev python-psycopg2 -y"
    elif db_type == "mongo":
        return "apt-get install mongodb mongodb-dev -y"
    elif db_type == "mysql":
        return "apt-get install mysql-server libmysqld-dev -y"
    elif db_type == "sqlite":
        return "apt-get install sqlite3 libsqlite3-dev -y"
    elif db_type is None:
        return None
    else:
        raise NotImplementedError("%s db installation command not defined" % db_type)


def get_username_pass(output):
    """
    Little routine to obtain 'safely' the username and the password
    :param stream output:
    :return:
    """
    dbuser = raw_input("Please specify the username for the DB access:")
    dbpass = getpass.getpass("Please enter the DB Password to use:")
    dbpass_conf = getpass.getpass("Please confirm the DB Password to use:")
    if not dbuser or not dbpass or not dbpass_conf or dbpass != dbpass_conf:
        output.write("Error in the password or user, please try again")
        return get_username_pass(output)
    return dbuser, dbpass


def get_db_preinstall_checks(dbtype, output, test=True):
    """
    render the DB pre setup script
    :param dbtype:
    :param stream output:
    :param bool test:
    :return:
    """
    t = get_template("db_pre_install_checks.sh")
    c = Context({"db_type": dbtype})
    fd, t_path = tempfile.mkstemp(suffix="preinstall.sh")
    with open(t_path, "w") as f:
        f.write(t.render(c))
    os.close(fd)
    os.chmod(t_path, 0o0755)
    if test:
        output.write(t.render(c))
    return t_path


def get_db_config_cmd(dbtype, dbname, dbuser, output, test=True):
    if not dbname:
        return None
    if dbtype == "postgres":
        tn = "postgres.sh"
        cmd = "su postgres -c"
    else:
        raise NotImplementedError("%s template not defined" % dbtype)
    t = get_template(tn)
    c = Context({"dbname": dbname, "username": dbuser})
    content = t.render(c)
    tf, t_path = tempfile.mkstemp(suffix=tn)
    with open(t_path, "w") as f:
        f.write(content)
    os.close(tf)
    os.chmod(t_path, 0o0755)
    if test:
        output.write(content)
    return " ".join([cmd, t_path])


def handle_db_pass(child, db_type, dbpass):
    """
    While the script to create the user is called, it's sometimes mandatory to pass the password
    :param child:
    :param str db_type:
    :param str dbpass:
    :return:
    """
    if db_type == "postgres":
        child.expect("password for new role:")
        child.sendline(dbpass)
        child.expect("it again:")
        child.sendline(dbpass)
    else:
        return None


def configure_database(db_type, dbname, output, test=True):
    """
    Run everything that is needed to install the DB
    :param db_type:
    :param dbname:
    :param stream output:
    :param bool test:
    :return:
    """
    if not db_type:
        return None, None
    output.write(">> Installing the DB")
    install_cmd = get_db_install_cmd(db_type)
    if not test:
        try:
            subprocess.check_call(install_cmd.split())
        except subprocess.CalledProcessError:
            raise CommandError("Issue while installing the DB")
    else:
        output.write(install_cmd)
    # get username and pass
    dbuser, dbpass = get_username_pass(output)

    # check if the user is already in the DB
    user_exists = False
    db_pre_checks = get_db_preinstall_checks(db_type, output, test)
    if not test:
        try:
            out = subprocess.check_output(db_pre_checks)
            output.write(out)
        except subprocess.CalledProcessError as err:
            output.write(err.output)
            raise CommandError("Failed to execute the pre-checks")
        if dbuser in out:
            user_exists = True
    # if not, add it and create the DB. Else, assume the DB already exists
    # in any case, if there is an error during this execution. it's going to be a nightmare...
    dbcmd = None
    if not user_exists:
        dbcmd = get_db_config_cmd(db_type, dbname, dbuser, output, test)
        if not test and dbcmd:
            try:
                child = pexpect.spawn(dbcmd)
                child.logfile_read = output
                handle_db_pass(child, db_type, dbpass)
            except Exception as err:
                output.write(err)
                raise CommandError("Failed to execute the DB user/DB setup")
    if not test and dbcmd:
        try:
            out = subprocess.check_output(db_pre_checks)
            output.write(out)
        except subprocess.CalledProcessError as err:
            output.write(err.output)
            raise CommandError("Failed to execute the pre-checks")
        if dbuser not in out:
            output.write("User was not added, please execute the command '%s' yourself" % dbcmd)
    return dbuser, dbpass
