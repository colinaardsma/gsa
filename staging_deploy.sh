#!/usr/bin/env bash
# chmod +x /path/to/yourscript/staging_deploy.sh to allow execution of script

# run using ./staging_deploy.sh from gsa folder

echo
echo ...PREPARING FOR DEPLOYMENT TO STAGING...

#echo ...COLLECTING STATIC FILES...
#python3 manage.py collectstatic

echo
echo ...SETTING ENVIRONMENT TO STAGING...
cat ./gsa/settings.staging.py > ./gsa/settings.py
cp ./gsa/settings.py ./.ebextensions/settings.py

echo
echo ...ADDING CHANGES TO COMMIT...
git add .

echo
echo ...COMMITTING CHANGES...
git commit -m "DEPLOY COMMIT `date +'%Y-%m-%d %H:%M:%S'`"

echo
echo ...PUSHING COMMIT...
git push

# gsa-dev is the name of the environment
echo
echo ...DEPLOYING...
eb deploy gsa-dev

# this needs to be the last line to set everything back to the dev env
echo
echo ...SETTING ENVIRONMENT BACK TO DEVELOPMENT...
cat ./gsa/settings.development.py > ./gsa/settings.py

