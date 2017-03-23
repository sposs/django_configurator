#!/bin/bash
export LC_ALL=$LANG
{% if not virtenv_exists %}
# create env directory
mkdir -p {{ workonhome }}
{% endif %}

# configure the virtual env
export WORKON_HOME={{ workonhome }}
source virtualenvwrapper.sh

mkdir -p {{ base_path_config }}/static


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

# finally install because we want to use the same django as the main app
pip install django_configurator

deactivate

exit ${install_status}
