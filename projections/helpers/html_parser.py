"""Projection HTML Parsing"""
import unicodedata
from urllib import request, parse
from datetime import datetime
from http.client import HTTPException
import pytz
from lxml import html, etree
import re

from .normalizer import name_normalizer, team_normalizer


def html_to_document(url, headers=None):
    """Get league standings\n
    Args:\n
        url: the url.\n
    Returns:\n
        html in document form.\n
    Raises:\n
        None.
    """
    if headers:
        req = request.Request(url, headers=headers)
    else:
        req = request.Request(url)
    while True:
        try:
            content = request.urlopen(req).read().decode('utf-8')
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
                single_player["name"] = name_team_pos[0]
                if len(name_team_pos) >= 3:
                    single_player["team"] = name_team_pos[2].replace(u'\xa0', u' ').encode('utf-8')
                else:
                    single_player["team"] = "NONE"
                if len(name_team_pos) >= 4:
                    name_team_pos[3] = name_team_pos[3].strip(" - ")
                    name_team_pos[3] = name_team_pos[3].strip(")")
                    single_player["pos"] = name_team_pos[3].replace(u'\xa0', u' ').encode('utf-8')
                else:
                    single_player["pos"] = "NONE"
                if len(name_team_pos) >= 5:
                    single_player["status"] = name_team_pos[4].replace(u'\xa0', '').encode('utf-8')
                else:
                    single_player["status"] = "ACTIVE"
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
    document = html_to_document(url, HEADERS)
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


def scrape_razzball(url):
    document = razzball_get_projection_page(url)
    table = document.xpath("//table[@id='neorazzstatstable']")
    headers = table[0].xpath("descendant::thead//th/text()")[1:]
    headers = [h.lower() for h in headers]
    body_rows = [tr.xpath("descendant::a/text()|descendant::td/text()") for tr in table[0].xpath("descendant::tbody//tr")]
    projection_dict = [dict(zip(headers, player)) for player in body_rows]
    if 'ip' in projection_dict[0]:
        projection_dict = [p for p in projection_dict if float(p['ip']) > 0.0]
    elif 'ab' in projection_dict[0]:
        projection_dict = [p for p in projection_dict if float(p['ab']) > 0.0]
    return projection_dict


def scrape_razzball_batters(url):
    batter_list = scrape_razzball(url)
    for batter in batter_list:
        # if batter['']
        if 'yahoo' in batter:
            batter['pos'] = batter['yahoo']
        elif 'y!' in batter:
            batter['pos'] = batter['y!']
        for key, value in batter.items():
            if not isinstance(value, list) and not isinstance(value, float) and not isinstance(value, int):
                try:
                    batter[key] = float(value)
                except ValueError:
                    pass

        batter['team'] = team_normalizer(batter['team'])
        if not batter['pos']:
            batter['pos'] = 'DH'
        elif not isinstance(batter['pos'], list):
            batter['pos'] = re.split('\W+', batter['pos'])
        if 'normalized_first_name' not in batter:
            norm_name = name_normalizer(batter['name'])
            batter['normalized_first_name'] = norm_name['First']
            batter['last_name'] = norm_name['Last']
        if 'isFA' not in batter:
            batter['isFA'] = False
        if 'keeper' not in batter:
            batter['keeper'] = 0.0
        if 'category' not in batter:
            batter['category'] = "batter"
        if 'status' not in batter:
            batter['status'] = ''
    return batter_list


def scrape_razzball_pitchers(url):
    pitcher_list = scrape_razzball(url)
    for pitcher in pitcher_list:
        if 'yahoo' in pitcher:
            pitcher['pos'] = pitcher['yahoo']
        elif 'y!' in pitcher:
            pitcher['pos'] = pitcher['y!']
        for key, value in pitcher.items():
            if not isinstance(value, list) and not isinstance(value, float) and not isinstance(value, int):
                try:
                    pitcher[key] = float(value)
                except ValueError:
                    pass

        pitcher['team'] = team_normalizer(pitcher['team'])
        if not pitcher['pos']:
            pitcher['pos'] = ['P']
        elif not isinstance(pitcher['pos'], list):
            pitcher['pos'] = re.split('\W+', pitcher['pos'])
        if 'normalized_first_name' not in pitcher:
            norm_name = name_normalizer(pitcher['name'])
            pitcher['normalized_first_name'] = norm_name['First']
            pitcher['last_name'] = norm_name['Last']
        if 'isFA' not in pitcher:
            pitcher['isFA'] = False
        if 'keeper' not in pitcher:
            pitcher['keeper'] = 0.0
        if 'is_sp' not in pitcher:
            pitcher['is_sp'] = True if 'SP' in pitcher['pos'] else False
        if 'category' not in pitcher:
            pitcher['category'] = "pitcher"
        if 'kip' not in pitcher:
            pitcher['kip'] = pitcher['k'] / pitcher['ip']
        if 'winsip' not in pitcher:
            pitcher['winsip'] = pitcher['w'] / pitcher['ip']
        if 'status' not in pitcher:
            pitcher['status'] = ''
    return pitcher_list


def scrape_closer_monkey():
    url = 'http://closermonkey.com/2015/05/04/updated-closer-depth-chart/'
    document = html_to_document(url, HEADERS)
    div = document.xpath("//div[@class='entry-content']")
    table = div[0].xpath("descendant::table")
    tr_list = table[0].xpath("descendant::tr")
    cl_list = []
    for tr in tr_list[1:len(tr_list) - 1]:
        td_list = tr.xpath("descendant::td/descendant-or-self::*/text()")
        team_one = team_normalizer(td_list[0])
        team_one_cl_one = {'last_name': td_list[1], 'team': team_one, 'pos': 'CL1'}
        team_one_cl_two = {'last_name': td_list[2], 'team': team_one, 'pos': 'CL2'}
        team_one_cl_three = {'last_name': td_list[3], 'team': team_one, 'pos': 'CL3'}
        if "*" in td_list[1]:
            team_one_cl_one['pos'] = 'CLC'
            team_one_cl_two['pos'] = 'CLC'
            team_one_cl_three['pos'] = 'CLC'
        cl_list.append(team_one_cl_one)
        cl_list.append(team_one_cl_two)
        cl_list.append(team_one_cl_three)
        team_two = team_normalizer(td_list[5])
        team_two_cl_one = {'last_name': td_list[6], 'team': team_two, 'pos': 'CL1'}
        team_two_cl_two = {'last_name': td_list[7], 'team': team_two, 'pos': 'CL2'}
        team_two_cl_three = {'last_name': td_list[8], 'team': team_two, 'pos': 'CL3'}
        if "*" in td_list[1]:
            team_two_cl_one['pos'] = 'CLC'
            team_two_cl_two['pos'] = 'CLC'
            team_two_cl_three['pos'] = 'CLC'
        cl_list.append(team_two_cl_one)
        cl_list.append(team_two_cl_two)
        cl_list.append(team_two_cl_three)
    return cl_list


def pretty_print_element(element):
    print(etree.tostring(element, encoding='unicode', pretty_print=True))


def pretty_print_to_file(element):
    text = etree.tostring(element, encoding='unicode', pretty_print=True)
    with open('html.txt', 'w') as outfile:
        print(text.encode('utf-8'), file=outfile)
    print("FILE OUTPUT COMPLETE")


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


HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) '
                         'Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
