===================
django_configurator
===================

:Date: 04/01/2017
:Author: Stephane Poss
:Copyright: 2012 - 2017 Xample Sàrl

Complete installation procedure
===============================

To install locally you need the following:

    - a configured postgres server (see at the end of this doc for details)
    - a configured mongodb installation
    - the following packages installed:

        - libgeos-dev
        - python-dev
        - libpq-dev (for psycopg2)
        - postgresql
        - mongodb
        - build-essential (on debian like)
        - pip (obtained from the get-pip.py that one can find on the web, ex.: https://bootstrap.pypa.io/get-pip.py )
        - pip install virtualenvwrapper

    - a directory `/opt/virtualenvs`
    - a directory `/opt/helitab` (writable by the user, readable by everyone), 2 files must be created:

        - `config.json`: it contains local installation host information (hostname, port, log path: should be `/logs/helitab.log`)
        - `settings.json`: local installation secrets, i.e. passwords and django secret key. This file should not be readable by the world.

    - a directory `/logs/` read-writable by all (the logs will end up here if you put then there in the `config.json` above)
    - a copy of the released application (e.g. `helitab_web-X.Y.Z.tar.gz`)

Once those are obtained, you can run::

    source virtualenvwrapper.sh
    export WORKON_HOME=/opt/virtualenvs
    mkvirtualenv helitab_web
    pip install helitab_web-X.Y.Z.tar.gz

If you've got everything set up properly, you should have no issues during installation. Use::

    cdsitepackages
    pwd

to determine the installation directory as you'll need it later to setup the server.
Let's call that directory the `install_dir`.

You also need to install the databases::

    python install_dir/helitab_web/manage.py migrate

If the database connection settings are right, the models will be applied to the DB. In particular, the `settings.json`
must contain the right password for the database.

Now quit the virtualenv with::

    deactivate

Now, there are several possibilities when it comes to the web server itself. There is the standalone mode and the
Apache mode.

Standalone mode
~~~~~~~~~~~~~~~

This mode implies that django runserver command is used. This also means the static files can't be served.
You then need to do the following:

    - install nginx
    - create a directory where you want and instruct nginx to look there
    - update `config.json` so that `STATIC_ROOT` has the same value as the directory name
    - run::

        source virtualenvwrapper.sh
        export WORKON_HOME=/opt/virtualenvs
        workon helitab_web
        python install_dir/helitab_web/manage.py collectstatic

  - This will collect all the static files found and copy then to the `STATIC_ROOT` directory.
  - restart nginx to start serving those files
  - update `config.json` and set the `STATIC_URL` value to the nginx server address

The static files being served by nginx, you can start the server with::

    source virtualenvwrapper.sh
    export WORKON_HOME=/opt/virtualenvs
    workon helitab_web
    python install_dir/helitab_web/manage.py runserver

This starts the server in the foreground and isn't very safe. I recommend you install the 'supervisor' program from your
favorite package distribution tool and configure it. It will allow to run the server as a service, gives automatic
restart capabilities in case of errors and even has a web frontend to restart a stuck service. It comes with some
security too. See http://supervisord.org/ for reference.

If everything goes fine, you should be able to access the service at the URL that was defined in the config.json.

In case the images are missing, it's certainly because the `STATIC_URL` is wrong. Check your nginx settings, update
the `config.json` and restart the django web server.

Apache mode
~~~~~~~~~~~

This mode can benefit from the standalone mode if you decide to use nginx to serve the static files. In such a case,
do the full nginx config above until the server restart. This changes slightly the Apache configuration.

Start by installing apache using your favorite package installation tool. Then install the mod_wsgi apache module.
It's called `libapache2-mod-wsgi` on debian-like platforms.

Then you can add the following configuration file in the `sites-enabled` directory of Apache::

    <VirtualHost yourhost:80>
        ServerAdmin some_admin@yourISP.country
        ServerName yourhost
        WSGIScriptAlias / /opt/virtualenvs/helitab_web/lib/python2.7/site-packages/helitab_web/wsgi.py
        # the following is necessary if NOT using nginx
        Alias /static /opt/virtualenvs/helitab_web/lib/python2.7/site-packages/core/static
        WSGIDaemonProcess helitab processes=2 threads=15 display-name=%{GROUP}
        WSGIProcessGroup helitab
        <Directory /opt/virtualenvs/helitab_web/lib/python2.7/site-packages/helitab_web/>
             <Files wsgi.py>
                  SetEnv downgrade-1.0
                  Order deny,allow
                  Allow from all
             </Files>
        </Directory>
    </VirtualHost>

Mind that the `VirtualHost` and `serverName` above matches the one you put in the `config.json` under
`HOST_BASE_DEFAULT`. Also, mind that the `000-default.conf` file does not conflict with the above.

Once this is done, you can restart the service with::

    service apache2 restart

And you should be able to access the server via the server URL you defined in the virtual host.

Check the `/var/logs/apache2/error.log` for any startup issues. Then check the helitab logs for specific issues (defined
in the `LOG_FILE_PATH` key of the `config.json` or `/logs/helitab.log` if you did not overwrite the value.

Standalone and connected-to-the-internet mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you are running the standalone mode, i.e. the file `/etc/xample/standalone_install` exists, you can also run the
addon synchronization tool. If you are connected to the internet, the tool is ran automatically, given that certain
utilities are installed and elements configured. Follow the following steps:

    - Install supervisor: `pip install supervisor`
    - Install apscheduler: `pip install apscheduler`
    - `mkdir /etc/supervisor`
    - Configure supervisor: `echo_supervisord_conf > /etc/supervisor/supervisord.conf`
    - Edit the configuration file so that the `[include]` block at the end is uncommented, and
      `files = /etc/supervisor/conf.d/*.conf`.
    - Add a file `/etc/supervisor/conf.d/helitab.conf` containing the following::

        [program:import]
        command=/opt/virtualenvs/helitab_web/bin/import_helitab_addons

    - The remaining part is to configure the automatic startup of supervisor when the machine starts. On debian systems,
      create a file `/etc/systemd/system/supervisor.service` containing the folllowing::

        [Unit]
        Description=supervisord - Supervisor process control system for UNIX
        Documentation=http://supervisord.org
        After=network.target

        [Service]
        Type=forking
        ExecStart=/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf
        ExecReload=/usr/local/bin/supervisorctl reload
        ExecStop=/usr/local/bin/supervisorctl shutdown

        [Install]
        WantedBy=multi-user.target

    - Then issue the following commands::

        systemctl enable supervisor
        systemctl start supervisor

    - Now when the machine starts, the 'agent' will be running automatically every hour.

This doc is partially taken from http://vicendominguez.blogspot.ch/2015/02/supervisord-in-centos-7-systemd-version.html


Updating the version
~~~~~~~~~~~~~~~~~~~~

In case a new version is made available, the tar ball will be distributed (I want to install localshop one day to
ease the process). Get it and run the following::

    source virtualenvwrapper.sh
    workon helitab_web
    pip install helitab_web.X.Y.Z.tar.gz

This will overwrite the existing installation. In case you're using Apache, there is nothing you need to do: mod_wsgi
will see that the wsgi file was modified and will restart directly the server.

If running standalone, you'll need to:

    - rerun the `collectstatic` command
    - kill and restart the service (trivial to do with supervisor).

This kind of update will be the easiest: there are no model changes, so no DB operations. In case there are model
changes (can happen in case of major django version changes), then you'll need to run::

    python install_dir/helitab_web/manage.py migrate

to get the new DB configured. As this can be a complex operation, make sure you have a backup of the DB ready. By the
way, this `migrate` only affects the postgres DB, as mongo does not need to handle migrations.


Installing postgres
~~~~~~~~~~~~~~~~~~~

Use your favorite package manager to install postgres, 9.4 seems to be fine. On debian like systems you get that with
`apt-get install postgresql`.

Log in the DB:

    - on debian::

        su - postgres
        psql

    - on ubuntu::

        sudo -u postgres psql

Then create the DB::

    create database helitab_web;
    grant all privileges on database helitab_web to postgres;
    alter role postgres with password 'SomeFancy_password'

Then make sure to keep that password in hand as you need to edit the `settings.json` file with that info (the `PG_PASS`
field).

Installing mongodb
~~~~~~~~~~~~~~~~~~

As with postgres, use your favorite package tool to install the mongodb package. On debian systems you can do that with
`apt-get install mongodb`.

Now to setup the right account/password do the following::

   mongo
   use helitab_web
   db.addUser({user:'helitab_web_admin', pwd:'SomeOtherFancyPwd', roles:["dbAdmin", "readWrite"]})

Use the password to populate the `MONGODB_PASS` option of the `settings.json` file.


Configuration settings
~~~~~~~~~~~~~~~~~~~~~~

The following gives the list of settings to be defined for a complete installation:

    - HOST_BASE_DEFAULT (mandatory): the IP or fully qualified host name (FQDN).
    - HOST_BASE_DEFAULT_PORT (optional): the port to use. Default: nothing, i.e. http default=80.
    - LOG_FILE_PATH (optional): the path here the logs are to be created. Default: `/logs/helitab.log`. Make sure
      the folder can be written to by the user running the server.
    - CATALOG_BASE_URL (mandatory): the base url for the catalog.
    - EMAIL_HOST (mandatory): the mail server.
    - EMAIL_PORT (optional): the smtp port. Default: "26".
    - EMAIL_HOST_USER (mandatory): the user account to use for the smtp connection.
    - EMAIL_HOST_PASSWORD (mandatory): the user password to use for the smtp connection.
    - SERVER_EMAIL (mandatory): the email address that error messages come from.
    - DEFAULT_FROM_EMAIL (mandatory): the default email address to use for various automated correspondence
      from the site manager(s).

Secret settings
~~~~~~~~~~~~~~~

The following are the secret keys that must be provided in `settings.json`. They are all mandatory:

    - SECRET_KEY: a long string used internally by django for the security features.
      Use http://www.miniwebtool.com/django-secret-key-generator/ to obtain one.
    - PG_USER: the postgres user that has access to the `helitab_web` database.
    - PG_PASS: the postgres user password.
    - MONGODB_PASS: the mongodb password for the `helitab_web_admin` user that has access to the `helitab_web` DB.
    - PAYPAL_IDENTITY_TOKEN: in case there is paypal, put its token. This must NEVER be made public.
