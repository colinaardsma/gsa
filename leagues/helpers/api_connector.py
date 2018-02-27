"""API Connecting and OAUTH\n
Functions:\n
    request_auth()\n
"""
import base64
from datetime import datetime, timezone, timedelta
import json
from urllib import parse, request
from http.client import HTTPException
import logging

from django.utils import timezone as djangotimezone

from leagues.models import update_profile
from gsa.settings import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# https://developer.yahoo.com/oauth2/guide/flows_authcode/


def request_auth(redirect_path):
    """Request Authentication from Yahoo!\n
    https://developer.yahoo.com/oauth2/guide/flows_authcode/#step-2-get-an-authorization-url-and-authorize-access\n
    Args:\n
        None.\n
    Returns:\n
        url to Yahoo! for authorization.\n
        Yahoo! will provide a code for entry in the next step.\n
    Raises:\n
        None.
    """
    url = 'https://api.login.yahoo.com/oauth2/request_auth'
    parameters = parse.urlencode({
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI + redirect_path,
        'response_type': 'code'
    })
    url += '?' + parameters
    req = request.Request(url)
    content = request.urlopen(req)
    return content.url


def get_token(authorization_code, redirect_path):
    """Request Token from Yahoo!\n
    https://developer.yahoo.com/oauth2/guide/flows_authcode/#step-4-exchange-authorization-code-for-access-token\n
    Args:\n
        authorization_code: Code provided by Yahoo! in request_auth() method.\n
    Returns:\n
        access_token, token_type, expires_in, refresh_token, xoauth_yahoo_guid in json form.\n
    Raises:\n
        None.
    """
    url = 'https://api.login.yahoo.com/oauth2/get_token'
    auth_string = '{}:{}'.format(CLIENT_ID, CLIENT_SECRET).encode()
    auth_header = base64.b64encode(auth_string)
    headers = {
        b'Authorization': b'Basic ' + auth_header,
        b'Content-Type': b'application/x-www-form-urlencoded'
    }
    body = parse.urlencode({
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI + redirect_path,
        'code': authorization_code
    }).encode('utf-8')
    req = request.Request(url, data=body, headers=headers)
    content = request.urlopen(req)
    raw_json = content.read()
    return raw_json


def yql_query(query_path, access_token):
    """YQL call to Yahoo! API\n
    Actually an alternative to the YQL call done through a URL.
    Args:\n
        query_path: YQL call translated to URL Path.\n
        access_token: json OAuth token returned in get_token().\n
    Returns:\n
        YQL data in XML format.\n
    Raises:\n
        None.
    """
    baseurl = "https://fantasysports.yahooapis.com/fantasy/v2"
    url = baseurl + query_path
    raw_json = get_json_data(url, access_token)
    return raw_json


def get_json_data(url, access_token):
    url = url + "?format=json"
    raw_json = get_xml_data(url, access_token)
    return raw_json


def get_xml_data(url, access_token):
    headers = {b'Authorization': b'Bearer ' + access_token.encode('utf-8'), b'request': b'None'}
    req = request.Request(url, headers=headers)
    while True:
        try:
            content = request.urlopen(req)
            raw_xml = content.read()
        except HTTPException as error:
            print(error)
            continue
        break
    return raw_xml


def check_token_expiration(user, redirect_path):
    """Check if Token is expired and if so refresh from Yahoo!\n
    https://developer.yahoo.com/oauth2/guide/flows_authcode/#step-4-exchange-authorization-code-for-access-token\n
    Args:\n
        user: The User DB model.\n
    Returns:\n
        access_token, token_type, expires_in, refresh_token, xoauth_yahoo_guid in json form.\n
    Raises:\n
        None.
    """
    token_expiration = user.profile.token_expiration.replace(tzinfo=None)
    now = datetime.now()
    if (not user or token_expiration - now).total_seconds() > 240:
        return
    url = 'https://api.login.yahoo.com/oauth2/get_token'
    auth_string = "{}:{}".format(CLIENT_ID, CLIENT_SECRET).encode()
    auth_header = base64.b64encode(auth_string)
    headers = {
        b'Authorization': b'Basic ' + auth_header,
        b'Content-Type': b'application/x-www-form-urlencoded'
    }
    body = parse.urlencode({
        'grant_type': 'refresh_token',
        'redirect_uri': REDIRECT_URI + redirect_path,
        'refresh_token': user.profile.refresh_token
    }).encode('utf-8')
    req = request.Request(url, data=body, headers=headers)
    content = request.urlopen(req)
    token_json = content.read()
    token_dict = json.loads(token_json)
    # print token_dict
    yahoo_guid = token_dict['xoauth_yahoo_guid']
    access_token = token_dict['access_token']
    refresh_token = token_dict['refresh_token']
    token_expiration = (datetime.now() +
                        timedelta(seconds=token_dict['expires_in']))
    updated_user = update_profile(user, yahoo_guid=yahoo_guid,
                                  access_token=access_token, refresh_token=refresh_token,
                                  token_expiration=token_expiration)
    return updated_user
