#!/usr/bin/env bash
export LC_ALL=$LANG
true;
{% if db_type == "postgres" %}
su postgres -c "psql -c 'SELECT usename FROM pg_user;'"
{% endif %}
exit $?;
