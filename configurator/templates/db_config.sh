#!/usr/bin/env bash
{%if dbconfig %}
su {{ dbconfig.user }} -c {{ dbconfig.script }}
db_setup=$?
if [ ${db_setup} != '0' ]; then
   exit ${db_setup}
fi
{% endif %}
exit 0;