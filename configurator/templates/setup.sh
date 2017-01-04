#!/bin/bash
{% if not virtenv_exists %}
# create env directory
mkdir -p {{ workonhome }}
{% endif %}
{% if server_install_cmd %}
# install requested server if needed
{{ server_install_cmd }}
install_res=$?
if [ ${install_res} != '0' ]; then
   # in case of error, exit
   exit ${install_res}
fi
{% endif %}
# configure the virtual env
export WORKON_HOME={{ workonhome }}
source virtualenvwrapper.sh
if [ $? != '0' ]; then
    pip install virtualenvwrapper.sh
    source virtualenvwrapper.sh
fi
# create the env or reuse
{% if make_env_dir %}
mkvirtualenv {{ project }}
{% else %}
workon {{ project }}
{% endif %}
# install or update
{% if update %}
pip install --upgrade --no-deps {{ project }}
pip install {{ project }}
{% else %}
pip install {{ requirement }}
{% endif %}
install_status=$?
deactivate
exit ${install_status}
