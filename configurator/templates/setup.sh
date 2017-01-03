#! /bin/bash
export WORKON_HOME={{ workonhome }}
source virtualenvwrapper.sh
if [ $? neq 0 ]; then
    pip install virtualenvwrapper.sh
    source virtualenvwrapper.sh
endif
mkvirtualenv {{ project }}
pip install {{ project }}

deactivate
