#!/usr/bin/env bash
export LC_ALL=$LANG
cd /tmp
createuser {{ username }} -P
cuser=$?
if [ ${cuser} != "0" ]; then
   exit ${cuser};
fi
createdb {{ dbname }} -O {{ username }}
cd -
exit $?;
