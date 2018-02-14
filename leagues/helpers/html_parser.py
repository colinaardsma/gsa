"""League HTML Parsing"""
from projections.helpers.normalizer import name_normalizer, team_normalizer
from projections.helpers.html_parser import html_to_document


def yahoo_players(league_no, b_or_p, max_players=300, all_players=False):
    """Parse FAs from yahoo league\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
        b_or_p: "B" for batters or "P" for pitchers.\n
        max_players: max number of players in list\n
        all_players: set to True to get all players, False to get all Available players\n
    Returns:\n
        list of available FAs for league specified.\n
    Raises:\n
        None.
    """
    status = "A"
    if all_players:
        status = "ALL"
    count = 0
    avail_player_list = []
    while count <= max_players:
        url = ("http://baseball.fantasysports.yahoo.com/b1/{league_no}" +
               "/players?status={status}&pos={b_or_p}&cut_type=33&stat1=S_S_2017&myteam=0&sort=AR&" +
               "sdir=1&count={count}").format(league_no=league_no, status=status,
                                              b_or_p=b_or_p.upper(), count=count)
        document = html_to_document(url)
        body_html = document.xpath(".//div[@class='players'][table]/table/tbody/tr")
        for player_html in body_html:
            single_player_html = player_html.xpath("descendant::td")
            player_stats = yahoo_player_dict_creator(single_player_html, b_or_p.upper())
            avail_player_list.append(player_stats)
        count += 25
    return avail_player_list


def yahoo_player_dict_creator(single_player_html, b_or_p):
    """Take in html table row for a single player and return stats in list form\n
    Args:\n
        single_player_html: html for a single player.\n
        b_or_p: "B" for batters or "P" for pitchers.\n
    Returns:\n
        dict of projections for a single player.\n
    Raises:\n
        None.
    """
    single_player = {}
    counter = 1
    counter_addition = 0
    if b_or_p == "B":
        dict_key_list = ["STARRED", "NAME", "NORMALIZED_FIRST_NAME", "LAST_NAME", "TEAM",
                         "POS", "OWNER", "GP", "PRESEASON_RANK", "CURRENT_RANK", "PCT_OWN",
                         "HAB", "R", "HR", "RBI", "SB", "OPS"]
        counter_addition = 1
    else:
        dict_key_list = ["STARRED", "NAME", "NORMALIZED_FIRST_NAME", "LAST_NAME", "TEAM",
                         "POS", "OWNER", "GP", "PRESEASON_RANK", "CURRENT_RANK", "PCT_OWN",
                         "IP", "W", "SV", "K", "ERA", "WHIP"]
    while counter < len(single_player_html) and counter < 15:
        if counter == 1:
            name = single_player_html[1].xpath("descendant::a[@class='Nowrap name F-link']" +
                                               "/text()")[0]
            if name is None:
                counter = len(single_player_html)
                continue
            single_player[dict_key_list[1]] = name
            team_pos = single_player_html[1].xpath("descendant::span[@class='Fz-xxs']" +
                                                   "/text()")[0]
            norm_name = name_normalizer(name)
            single_player[dict_key_list[2]] = norm_name['First']
            single_player[dict_key_list[3]] = norm_name['Last']
            single_player[dict_key_list[4]] = team_pos.split(" - ")[0].upper()
            single_player[dict_key_list[5]] = team_pos.split(" - ")[1]
            dl_na = single_player_html[1].xpath("descendant::span[@class='ysf-player-status " +
                                                "F-injury Fz-xxs Grid-u Lh-xs Mend-xs']" +
                                                "/text()")
            if not dl_na:
                single_player["DL_NA_STATUS"] = False
            else:
                single_player["DL_NA_STATUS"] = dl_na[0]
            counter = 9
            continue

        else:
            stat = single_player_html[counter + counter_addition].xpath("descendant::*/text()")
            if len(stat) != 0:
                single_player[dict_key_list[counter]] = stat[0]
        counter += 1
    return single_player


def yahoo_teams(league_no):
    """Parse teams from yahoo league\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        list of teams based on league number.\n
    Raises:\n
        None.
    """
    team_list = []
    url = ("http://baseball.fantasysports.yahoo.com/b1/" + str(league_no) +
           "/startingrosters")
    document = html_to_document(url)
    team_divs = document.xpath(".//div[@class='Bd']/div")
    for team in team_divs:
        team_dict = yahoo_team_creator(team)
        team_list.append(team_dict)
    return team_list


def yahoo_team_creator(single_team_html):
    """Create team. Includes name, number, and roster (list)\n
    Args:\n
        single_team_html: html for a single team.\n
    Returns:\n
        dict of team including name, number, and roster as a list.\n
    Raises:\n
        None.
    """
    team = {}
    dict_key_list = ["TEAM_NAME", "TEAM_NUMBER", "ROSTER"]
    team[dict_key_list[0]] = str(single_team_html.xpath(".//p/a[@href]/text()")[0])
    team_number_a = single_team_html.xpath(".//p/a")[0]
    team[dict_key_list[1]] = team_number_a.attrib['href'].split("/")[3]
    table_body = single_team_html.xpath(".//table/tbody")
    for row in table_body:
        roster = []
        player_div = row.xpath(".//tr/td[@class='player']/div[1]/div")
        # html_player = row.xpath(".//tr/td[@class='player']/div[1]/div/a/text()")
        # html_team = row.xpath(".//tr/td[@class='player']/div[1]/div/span/text()")
        for player in player_div:
            player_dict = {}
            player_name = player.xpath(".//a/text()")
            player_team = player.xpath(".//span/text()")
            if player_team[0] == "(Empty)":
                continue
            string_loc = player_team[0].find(" - ")
            player_team = player_team[0][:string_loc]
            norm_name = name_normalizer(player_name[0])
            player_dict['NAME'] = player_name[0]
            player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
            player_dict["LAST_NAME"] = norm_name['Last']
            player_dict['TEAM'] = team_normalizer(player_team.upper())
            # player = player.replace('.', '')
            roster.append(player_dict)
        team[dict_key_list[2]] = roster
    return team


def get_single_yahoo_team(league_no, team_name=None, team_number=None):
    """Get single team from yahoo team list. Using either team name or team number.\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
        team_name: name of the team to retreive (default = None).
        team_number: number of the team to retreive (default = None).
    Returns:\n
        dict of single team.\n
    Raises:\n
        None.
    """
    team_list = yahoo_teams(league_no)
    print(league_no)
    print(team_list)
    print(team_name)
    print(team_number)
    for team in team_list:
        if team_number is not None and team['TEAM_NUMBER'] == str(team_number):
            return team
        elif team_name is not None and team['TEAM_NAME'].lower() == team_name.lower():
            return team
    print("Team Name or Team Number are invalid.")


def get_standings(league_no, team_count):
    """Get league standings\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
        team_count: number of teams in league.\n
    Returns:\n
        list of dict of current team standings.\n
    Raises:\n
        None.
    """
    url = ("http://baseball.fantasysports.yahoo.com/b1/" + str(league_no) +
           "/standings?opt_out=1")
    document = html_to_document(url)
    points_html = document.xpath(".//section[@id='standings-table']/table")[0]
    points_headers = points_html.xpath(".//thead/tr[@class='Alt Last']//text()")
    points_header_list = []
    for header_html in points_headers:
        if header_html == u"\ue004":
            continue
        header = "Points" + header_html.replace(" ", "")
        points_header_list.append(header)
    points_teams = points_html.xpath(".//tbody/tr")
    stats_html = document.xpath(".//section[@id='standings-table']/table")[1]
    stats_headers = stats_html.xpath(".//thead/tr[@class='Alt Last']//text()")
    stats_header_list = []
    for header_html in stats_headers:
        if header_html == u"\ue004":
            continue
        header = "Stats" + header_html.replace(" ", "")
        stats_header_list.append(header)
    stats_teams = stats_html.xpath(".//tbody/tr")
    current_standings = []
    html_counter = 0
    while html_counter < team_count:
        team_dict = {}
        team_points_row = points_teams[html_counter].xpath(".//descendant::text()")
        team_stats_row = stats_teams[html_counter].xpath(".//descendant::text()")
        team_points_row[0] = team_points_row[0].replace(".", "")
        team_stats_row[0] = team_stats_row[0].replace(".", "")
        points_counter = 0
        while points_counter < len(points_header_list):
            team_dict[points_header_list[points_counter]] = team_points_row[points_counter]
            points_counter += 1
        stats_counter = 0
        while stats_counter < len(stats_header_list):
            cleaned_stat = team_stats_row[stats_counter].replace("*", "")
            team_dict[stats_header_list[stats_counter]] = cleaned_stat
            stats_counter += 1
        current_standings.append(team_dict)
        html_counter += 1
    return current_standings

# def single_team_standing_dict(league_no, current_standings, team_name=None, team_number=None):
#     """Get league standings\n
#     Args:\n
#         league_no: Yahoo! fantasy baseball league number.\n
#         current_standings: dict of the current league standings.\n
#     Returns:\n
#         list of dict of projected final team standings.\n
#     Raises:\n
#         None.
#     """
#     projected_final_standings = []
#     team_list = yahoo_teams(league_no)
#     return projected_final_standings


def get_league_settings(league_no):
    """Get league settings\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        dict of league settings.\n
    Raises:\n
        None.
    """
    url = ("http://baseball.fantasysports.yahoo.com/b1/" + str(league_no) +
           "/settings")
    document = html_to_document(url)
    settings_table = document.xpath(".//table[@id='settings-table']/tbody")[0]
    league_settings = {}
    settings_rows = settings_table.xpath(".//tr")
    for setting in settings_rows:
        key = setting.xpath(".//td/text()")[0].encode('utf-8').strip().replace('\xc2\xa0', ' ')
        if key == "League Logo:":
            continue
        value = setting.xpath(".//td/b/text()")[0].encode('utf-8').strip().replace('\xc2\xa0', ' ')
        league_settings[key] = value
    return league_settings


def split_league_pos_types(league_roster_pos):
    """Turn full list of league roster spots into list split into batting, pitching, bench, dl, na\n
    Args:\n
        league_roster_pos: list of roster spots\n
    Returns:\n
        dict of roster spots by type (batting, pitching, bench, dl, na.\n
    Raises:\n
        None.
    """
    batting_pos = []
    pitching_pos = []
    bench_pos = []
    dl_pos = []
    na_pos = []
    all_pos = league_roster_pos.split(", ")
    while "SP" in all_pos:
        pitching_pos.append("SP")
        all_pos.remove("SP")
    while "RP" in all_pos:
        pitching_pos.append("RP")
        all_pos.remove("RP")
    while "P" in all_pos:
        pitching_pos.append("P")
        all_pos.remove("P")
    while "BN" in all_pos:
        bench_pos.append("BN")
        all_pos.remove("BN")
    while "DL" in all_pos:
        dl_pos.append("DL")
        all_pos.remove("DL")
    while "NA" in all_pos:
        na_pos.append("NA")
        all_pos.remove("NA")
        batting_pos = all_pos
    league_roster_pos_dict = {"Batting POS": batting_pos, "Pitching POS": pitching_pos, "Bench POS": bench_pos,
                              "DL POS": dl_pos, "NA POS": na_pos}
    return league_roster_pos_dict
