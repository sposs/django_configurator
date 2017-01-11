#!/usr/bin/env bash
export LC_ALL=$LANG
{% if server_install_cmd %}
# install requested server if needed
{{ server_install_cmd }}
install_res=$?
if [ ${install_res} != '0' ]; then
   # in case of error, exit
   exit ${install_res}
fi
{% else %}
#no server dependencies to install
{% endif %}
exit 0;
