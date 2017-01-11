#!/usr/bin/env bash
export LC_ALL=$LANG
{% if db_install_cmd %}
{{ db_install_cmd }}
{% endif %}
exit 0;
