#!/usr/bin/env bash
# chmod +x /path/to/yourscript/run_local.sh to allow execution of script

# run using ./run_local.sh from gsa folder

echo
echo ...RUNNING APPLICATION LOCALLY...

echo
echo ...SETTING ENVIRONMENT TO DEVELOPMENT...
cat ./gsa/settings.development.py > ./gsa/settings.py

echo
echo ...STARTING POSTGRES DB...
pg_ctl start -D /Users/colin.aardsma/Library/Application\ Support/Postgres/var-10

echo
echo ...STARTING SERVER...
python3 manage.py runserver localhost:8080

# to stop psql
# pg_ctl stop -D /Users/colin.aardsma/Library/Application\ Support/Postgres/var-10
