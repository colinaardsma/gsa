"""Projection HTML Parsing"""
import unicodedata
from lxml import html
from http.client import HTTPException
import urllib


def html_to_document(url):
    """Get league standings\n
    Args:\n
        url: the url.\n
    Returns:\n
        html in document form.\n
    Raises:\n
        None.
    """
    request = urllib.request.Request(url)
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
