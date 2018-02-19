"""Projection HTML Parsing"""
import unicodedata
import urllib
from datetime import datetime
from http.client import HTTPException
import pytz
from lxml import html


def html_to_document(url, headers=None):
    """Get league standings\n
    Args:\n
        url: the url.\n
    Returns:\n
        html in document form.\n
    Raises:\n
        None.
    """
    request = urllib.request.Request(url, headers=headers)
    while True:
        try:
            content = urllib.request.urlopen(request).read().decode('utf-8')
        except HTTPException:
            print(HTTPException)
            continue
        break
    decoded_content = unicodedata.normalize('NFKD', content).encode('ASCII', 'ignore')
    document = html.document_fromstring(decoded_content)
    return document


def fantasy_pro_players(url):
    """Parse batter data from url\n
    Args:\n
        url: the fantasypros.com url.\n
    Returns:\n
        list of dict of player projections.\n
    Raises:\n
        None.
    """
    document = html_to_document(url)
    headings_list_html = document.xpath("//div[@class='mobile-table']" +
                                        "/table/thead/tr/descendant::*/text()")
    headings_list_html[len(headings_list_html) - 1] = "AVG_OWN_PCT"
    headings_list_html.append("YAHOO_OWN_PCT")
    headings_list_html.append("ESPN_OWN_PCT")
    body_html = document.xpath("//div[@class='mobile-table']/table/tbody/tr")
    player_list = []
    for player_html in body_html:
        single_player_html = player_html.xpath("descendant::td")
        player_stats = fant_pro_player_dict_creator(single_player_html, headings_list_html)
        if player_stats:
            player_list.append(player_stats)
    return player_list


def fant_pro_player_dict_creator(single_player_html, headings_list_html):
    """Take in html table row for a single player and return player data and
    stats in dictionary form.\n
    Args:\n
        single_player_html: html for a single player.\n
        headings_list_html: html for the table heading row.\n
    Returns:\n
        dict of projections for a single player.\n
    Raises:\n
        None.
    """
    single_player = {}
    counter = 0
    name_team_pos = single_player_html[1].xpath("descendant::*/text()")
    if name_team_pos:
        while counter < len(single_player_html):
            if counter == 1:
                if name_team_pos[0] is None or name_team_pos[0] == " ()":
                    counter = len(single_player_html)
                    continue
                single_player["NAME"] = name_team_pos[0]
                if len(name_team_pos) >= 3:
                    single_player["TEAM"] = name_team_pos[2].replace(u'\xa0', u' ').encode('utf-8')
                else:
                    single_player["TEAM"] = "NONE"
                if len(name_team_pos) >= 4:
                    name_team_pos[3] = name_team_pos[3].strip(" - ")
                    name_team_pos[3] = name_team_pos[3].strip(")")
                    single_player["POS"] = name_team_pos[3].replace(u'\xa0', u' ').encode('utf-8')
                else:
                    single_player["POS"] = "NONE"
                if len(name_team_pos) >= 5:
                    single_player["STATUS"] = name_team_pos[4].replace(u'\xa0', '').encode('utf-8')
                else:
                    single_player["STATUS"] = "ACTIVE"
            else:
                stat = single_player_html[counter].xpath("self::*/text()")
                if len(stat) != 0:
                    cat = stat[0].replace(u'\xa0', '').encode('utf-8')
                    single_player[headings_list_html[counter]] = cat
            counter += 1
        return single_player


def parse_pos_from_url(playerid):
    """Parse position data from fangraphs website using playerid\n
    SUPER SLOW!\n
    Args:\n
        playerid: the playerid from csv\n
    Returns:\n
        list of player's eligible positions\n
    Raises:\n
        None.
    """
    url = 'http://www.fangraphs.com/statss.aspx?playerid=' + str(playerid)
    document = html_to_document(url)
    raw_pos = document.xpath('.//strong[text()="Position:"]')[0].tail
    pos = raw_pos.strip().split("/")
    return pos


def razzball_get_projection_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
    document = html_to_document(url, headers)
    return document


# TODO: this would be a great async test, render the user page in foreground and wait on razzball reply
def razzball_get_update_datetime(url):
    document = razzball_get_projection_page(url)
    # update_string = document.xpath("//abbr[@class='entry-date published updated']")[0].text
    update_string = document.xpath("//abbr[@class='entry-date published updated']/text()")[0]
    tz_offest = timezone_switch_case(update_string[-3:])
    offset_string = update_string[:-3] + tz_offest
    update_datetime = datetime.strptime(offset_string, '%Y-%m-%d %I:%M:%S %p %z')

    return update_datetime


def timezone_switch_case(tz_string):
    switcher = {"EDT": '-0400',
                "EST": '-0500',
                "CDT": '-0500',
                "CST": '-0600',
                'MDT': '-0600',
                'MST': '-0700',
                'PDT': '-0700',
                'PST': '-0800'}
    return switcher.get(tz_string, '-0000')
