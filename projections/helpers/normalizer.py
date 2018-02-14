"""Normalize text"""
import re


def name_normalizer(full_name):
    name_list = {'chris': ['chris', 'christopher', 'topher'],
                 'alex': ['alex', 'alexander'],
                 'ken': ['ken', 'kenneth'],
                 'jake': ['jake', 'jacob'],
                 'greg': ['greg', 'gregory'],
                 'matt': ['matt', 'matthew'],
                 'brad': ['brad', 'bradley'],
                 'mike': ['mike', 'michael'],
                 'john': ['john', 'jon', 'johnny', 'johnathan'],
                 'dan': ['dan', 'danny', 'daniel'],
                 'steve': ['steve', 'steven', 'stephen'],
                 'bill': ['bill', 'billy', 'will', 'william'],
                 'charlie': ['charlie', 'chuck', 'charles'],
                 'tony': ['tony', 'anthony'],
                 'zack': ['zack', 'zach', 'zachary'],
                 'manny': ['manny', 'manuel'],
                 'tom': ['tom', 'tommy', 'thomas'],
                 'dave': ['dave', 'david'],
                 'josh': ['josh', 'joshua'],
                 'drew': ['drew', 'andy', 'andrew'],
                 'fred': ['fred', 'freddie', 'freddy', 'frederick'],
                 'scott': ['scott', 'scotty', 'scottie'],
                 'sam': ['sam', 'sammy', 'sammie', 'samuel'],
                 'jim': ['jim', 'jimmy', 'jimmie', 'james'],
                 'joe': ['joe', 'joey', 'joseph'],
                 'bran': ['bran', 'brand', 'brandon'],
                 'javy': ['javy', 'javier'],
                 'rob': ['rob', 'robbie', 'bob', 'bobbie', 'bobby', 'robert'],
                 'sal': ['sal', 'salvador'],
                 'al': ['al', 'allen', 'alan', 'allan', 'albert'],
                 'vince': ['vince', 'vincent']}
    if full_name is None:
        return {'First': "", 'Last': "", 'Full': ""}
    original_full_name = str(full_name)
    full_name = full_name.replace(".", "").lower()
    groups = regex_groups(full_name)
    first_name = groups.group(1)
    last_name = groups.group(2).strip()
    norm_first_name = first_name
    for key, val in name_list.items():
        if first_name in val:
            norm_first_name = key
            break
    # normalized_full_name = norm_first_name.capitalize() + ' ' + last_name.capitalize()
    name = {'First': norm_first_name, 'Last': last_name, 'Full': original_full_name}
    return name


def team_normalizer(team):
    team_list = {'LAA': ['LAA', 'AN', 'ANA', 'ANGELS'],
                 'ARI': ['ARI', 'DIAMONDBACKS'],
                 'ATL': ['ATL', 'BRAVES'],
                 'BAL': ['BAL', 'ORIOLES'],
                 'BOS': ['BOS', 'RED SOX'],
                 'CHW': ['CHW', 'CHA', 'CWS', 'WHITE SOX'],
                 'CHC': ['CHC', 'CHN', 'CUBS'],
                 'CIN': ['CIN', 'REDS'],
                 'CLE': ['CLE', 'INDIANS'],
                 'COL': ['COL', 'ROCKIES'],
                 'DET': ['DET', 'TIGERS'],
                 'FA': ['FA', 'FREE AGENT'],
                 'MIA': ['MIA', 'FLO', 'FL', 'MARLINS'],
                 'HOU': ['HOU', 'ASTROS'],
                 'KC': ['KC', 'KCA', 'ROYALS'],
                 'LAD': ['LAD', 'LAN', 'LA', 'DODGERS'],
                 'MIL': ['MIL', 'BREWERS'],
                 'MIN': ['MIN', 'TWINS'],
                 'NYY': ['NYY', 'NYA', 'YANKEES'],
                 'NYM': ['NYM', 'NYN', 'METS'],
                 'OAK': ['OAK', 'ATHLETICS'],
                 'PHI': ['PHI', 'PHILLIES'],
                 'PIT': ['PIT', 'PIRATES'],
                 'SD': ['SD', 'SDN', 'PADRES'],
                 'SEA': ['SEA', 'MARINERS'],
                 'SF': ['SF', 'SFN', 'GIANTS'],
                 'STL': ['STL', 'SLN', 'CARDINALS'],
                 'TB': ['TB', 'TBA', 'RAYS'],
                 'TEX': ['TEX', 'RANGERS'],
                 'TOR': ['TOR', 'BLUE JAYS'],
                 'WAS': ['WAS', 'WSH', 'NATIONALS'],
                 'NONE': ['NONE']}
    team = team.upper()
    for key, val in team_list.items():
        if team in val:
            team = key
    return team


def name_checker(name_a, name_b):
    """Checks first names against nicknames/shortened names\n
    Args:\n
        source_name: full name of the source player\n
        destination_name: full name of the destination player\n
    Returns:\n
        True if match\n
    Raises:\n
        None.
    """
    name_a_chars = name_char_pair_creator(name_a)
    name_b_chars = name_char_pair_creator(name_b)
    similarity = name_char_pair_comparer(name_a_chars, name_b_chars)
    match = False
    if similarity > 60.0:
        match = True
    return match


def name_char_pair_creator(name):
    """Checks first names against nicknames/shortened names\n
    Args:\n
        name (str): full name of the source player\n
    Returns:\n
        (list) of the name's character pairs\n
    Raises:\n
        None.
    """
    name = name.strip().lower()
    name = re.sub(r"\W", "", name).strip()
    char_pair_list = []
    i = 0
    while i < len(name) - 1:
        char_pair = name[i] + name[i + 1]
        char_pair_list.append(char_pair)
        i += 1
    return char_pair_list


def name_char_pair_comparer(name_a_chars, name_b_chars):
    """Checks first names against nicknames/shortened names\n
    Args:\n
        name_a_chars (list): list of the name's character pairs\n
        name_b_chars (list): list of the name's character pairs\n
    Returns:\n
        (float) percentage of match value\n
    Raises:\n
        None.
    """
    match_counter = 0
    total_pairs = len(name_a_chars) + len(name_b_chars)
    for a_pair in name_a_chars:
        for b_pair in name_b_chars:
            if a_pair == b_pair:
                match_counter += 1
    match_value = (float(match_counter) / float(total_pairs)) * 100.0 * 2.0
    return match_value


def name_comparer(name_a, name_b):
    name_list = {'chris': ['chris', 'christopher', 'topher'],
                 'alex': ['alex', 'alexander'],
                 'ken': ['ken', 'kenneth'],
                 'jake': ['jake', 'jacob'],
                 'greg': ['greg', 'gregory'],
                 'matt': ['matt', 'matthew'],
                 'brad': ['brad', 'bradley'],
                 'mike': ['mike', 'michael'],
                 'john': ['john', 'jon', 'johnny', 'johnathan'],
                 'dan': ['dan', 'danny', 'daniel'],
                 'steve': ['steve', 'steven', 'stephen'],
                 'bill': ['bill', 'billy', 'will', 'william'],
                 'charlie': ['charlie', 'chuck', 'charles'],
                 'tony': ['tony', 'anthony'],
                 'zack': ['zack', 'zach', 'zachary'],
                 'manny': ['manny', 'manuel'],
                 'tom': ['tom', 'tommy', 'thomas'],
                 'dave': ['dave', 'david'],
                 'josh': ['josh', 'joshua'],
                 'drew': ['drew', 'andy', 'andrew'],
                 'fred': ['fred', 'freddie', 'freddy', 'frederick'],
                 'scott': ['scott', 'scotty', 'scottie'],
                 'sam': ['sam', 'sammy', 'sammie', 'samuel'],
                 'jim': ['jim', 'jimmy', 'jimmie', 'james'],
                 'joe': ['joe', 'joey', 'joseph'],
                 'bran': ['bran', 'brand', 'brandon'],
                 'javy': ['javy', 'javier'],
                 'rob': ['rob', 'robbie', 'bob', 'bobbie', 'bobby', 'robert'],
                 'sal': ['sal', 'salvador'],
                 'al': ['al', 'allen', 'alan', 'allan', 'albert'],
                 'vince': ['vince', 'vincent']}
    name_a = name_a.replace(".", "").lower()
    name_b = name_b.replace(".", "").lower()
    if name_a == name_b:
        return True
    name_a_groups = regex_groups(name_a)
    name_a_first = name_a_groups.group(1)
    name_a_last = name_a_groups.group(2)
    name_a_norm = name_a_first
    name_b_groups = regex_groups(name_b)
    name_b_first = name_b_groups.group(1)
    name_b_last = name_b_groups.group(2)
    name_b_norm = name_b_first
    if name_a_last != name_b_last:
        return False
    for key, val in name_list.items():
        if name_a_first in val:
            name_a_norm = key
        if name_b_first in val:
            name_b_norm = key
    if name_a_norm == name_b_norm:
        return True
    return False


def team_comparer(team_a, team_b):
    team_list = {'LAA': ['LAA', 'AN', 'ANA'],
                 'ARI': ['ARI'],
                 'ATL': ['ATL'],
                 'BAL': ['BAL'],
                 'BOS': ['BOS'],
                 'CHW': ['CHW', 'CHA', 'CWS'],
                 'CHC': ['CHC', 'CHN'],
                 'CIN': ['CIN'],
                 'CLE': ['CLE'],
                 'COL': ['COL'],
                 'DET': ['DET'],
                 'FA': ['FA'],
                 'MIA': ['MIA', 'FLO', 'FL'],
                 'HOU': ['HOU'],
                 'KC': ['KC', 'KCA'],
                 'LAD': ['LAD', 'LAN', 'LA'],
                 'MIL': ['MIL'],
                 'MIN': ['MIN'],
                 'NYY': ['NYY', 'NYA'],
                 'NYM': ['NYM', 'NYN'],
                 'OAK': ['OAK'],
                 'PHI': ['PHI'],
                 'PIT': ['PIT'],
                 'SD': ['SD', 'SDN'],
                 'SEA': ['SEA'],
                 'SF': ['SF', 'SFN'],
                 'STL': ['STL', 'SLN'],
                 'TB': ['TB', 'TBA'],
                 'TEX': ['TEX'],
                 'TOR': ['TOR'],
                 'WAS': ['WAS', 'WSH']}
    team_a = team_a.upper()
    team_b = team_b.upper()
    team_a_norm = "a"
    team_b_norm = "b"
    if team_a == team_b:
        return True
    for key, val in team_list.items():
        if team_a in val:
            team_a_norm = key
        if team_b in val:
            team_b_norm = key
    if team_a_norm == team_b_norm:
        return True
    return False


def player_comparer(yahoo_player, proj_player):
    if (yahoo_player['LAST_NAME'] == proj_player.last_name and
            yahoo_player['TEAM'] == proj_player.team and
            yahoo_player['NORMALIZED_FIRST_NAME'] == proj_player.normalized_first_name):
        return True
    return False


def regex_groups(full_name):
    groups = re.search(r'^([\w-]*)(.*?(?=\sjr)|.*)(\sjr)?', full_name)
    return groups

# NAME_A = "Joe H. Smith"
# NAME_B = "Joseph Smith"
# NAME_C = "Joe Smith"
# NAME_D = "Jorge De La Rosa"
# NAME_E = "Rubby De La Rosa"
# CHARS_A = name_char_pair_creator(NAME_A)
# CHARS_B = name_char_pair_creator(NAME_B)
# CHARS_C = name_char_pair_creator(NAME_C)
# CHARS_D = name_char_pair_creator(NAME_D)
# CHARS_E = name_char_pair_creator(NAME_E)
# print CHARS_A
# print CHARS_C
# print name_char_pair_comparer(CHARS_D, CHARS_E)

# print name_checker(NAME_D, NAME_E)
# # # 60

# print name_normalizer('Ken Giles Jr.')
