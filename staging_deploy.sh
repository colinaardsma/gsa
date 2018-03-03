#!/usr/bin/env bash
# chmod +x /path/to/yourscript/staging_deploy.sh to allow execution of script

# run using ./staging_deploy.sh from gsa folder

echo Preparing for deployment to staging

ln -s -f settings.staging.py settings.py

# gsa-dev is the name of the environment
eb deploy gsa-dev

# this needs to be the last line to set everything back to the dev env
ln -s -f settings.development.py settings.py

