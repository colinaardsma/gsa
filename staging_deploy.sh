#!/usr/bin/env bash
# chmod +x /path/to/yourscript/staging_deploy.sh to allow execution of script

# run using ./staging_deploy.sh from gsa folder

echo ...PREPARING FOR DEPLOYMENT TO STAGING...

#echo ...COLLECTING STATIC FILES...
#python3 manage.py collectstatic

echo ...SETTING ENVIRONMENT TO STAGING...
cat ./gsa/settings.staging.py > ./gsa/settings.py

#echo ...COMMITTING CHANGES...
#
#echo ...PUSHING COMMIT...

# gsa-dev is the name of the environment
echo ...DEPLOYING...
eb deploy gsa-dev

# this needs to be the last line to set everything back to the dev env
echo ...SETTING ENVIRONMENT BACK TO DEVELOPMENT...
cat ./gsa/settings.development.py > ./gsa/settings.py

