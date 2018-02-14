"""CSV Parser"""
import csv
import pprint

from .normalizer import team_normalizer, name_normalizer


def parse_batters_from_csv(user, league, csv_file):
    """Parse batter data from CSV file\n
    Args:\n
        csv_file: the CSV file.\n
    Returns:\n
        list of dict of player projections.\n
    Raises:\n
        None.
    """
    batter_dict_list = []
    reader = csv.DictReader(csv_file)
    for row in reader:
        batter = {}
        name = ''
        if 'Name' in row:
            name = row["Name"]
            # name = row["Name"].decode('utf-8').replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c", "").replace(u"\u201d", "")
        elif '\xef\xbb\xbf"Name"' in row:
            name = row['\xef\xbb\xbf"Name"']
            # name = row['\xef\xbb\xbf"Name"'].decode('utf-8').replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c", "").replace(u"\u201d", "")

        if ((row['AB'] is not None and float(row['AB']) == 0.0) or
                (row['OPS'] is not None and float(row['OPS']) == 0.000) or
                (row['AVG'] is not None and float(row['AVG']) == 0.000) or
                (name is None or name == '') or float(row['G']) <= 0.0):
            # or not row["POS"]):
            continue

        norm_name = name_normalizer(name)
        pos = []
        status = ""

        if 'YAHOO' in row:
            pos = row['YAHOO'].split('/')
            # pos = row['YAHOO'].decode('utf-8').split('/')
        batter['isFA'] = False
        batter['keeper'] = 0.0
        batter['name'] = name
        batter['normalized_first_name'] = norm_name['First']
        batter['last_name'] = norm_name['Last']
        batter['team'] = (team_normalizer(row['Team'])
                          if row['Team'] else "FA")
        # batter['team'] = (team_normalizer(row['Team'].decode('utf-8'))
        #                   if row['Team'] else "FA")
        batter['pos'] = pos
        batter['status'] = status
        batter['category'] = "batter"
        batter['ab'] = float(row['AB'])
        batter['pa'] = float(row['PA'])
        batter['r'] = float(row['R'])
        batter['hr'] = float(row['HR'])
        batter['rbi'] = float(row['RBI'])
        batter['sb'] = float(row['SB'])
        batter['avg'] = float(row['AVG'])
        batter['ops'] = float(row['OPS'])
        batter['g'] = float(row['G'])
        # for cat in questionable_float_cats:
        #     if cat in row:
        #         batter[cat] = float(row[cat])
        # for cat in questionable_string_cats:
        #     if cat in row:
        #         batter[cat] = str(row[cat])
        batter_dict_list.append(batter)
    return batter_dict_list


def parse_pitchers_from_csv(user, league, csv_file):
    """Parse pitcher data from CSV file\n
    Args:\n
        csv_file: the CSV file.\n
    Returns:\n
        list of dict of player projections.\n
    Raises:\n
        None.
    """
    pitcher_dict_list = []
    reader = csv.DictReader(csv_file)
    max_ip = 0.0
    for row in reader:
        if float(row['IP']) > max_ip:
            max_ip = float(row['IP'])
    csv_file.seek(0)
    reader2 = csv.DictReader(csv_file)
    for row in reader2:
        pitcher = {}
        name = ''
        if 'Name' in row:
            name = row["Name"]
            # name = row["Name"].decode('utf-8').replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c", "").replace(u"\u201d", "")
        elif '\xef\xbb\xbf"Name"' in row:
            name = row['\xef\xbb\xbf"Name"']
            # name = row['\xef\xbb\xbf"Name"'].decode('utf-8').replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c", "").replace(u"\u201d", "")

        if (row['IP'] is None or float(row['IP']) <= (max_ip * 0.05) or
                row['W'] is None or float(row['W']) < 0.0 or
                row['SV'] is None or float(row['SV']) < 0.0 or
                row['K'] is None or float(row['K']) < 0.0 or
                row['ERA'] is None or float(row['ERA']) <= 0.0 or
                row['WHIP'] is None or float(row['WHIP']) <= 0.0 or
                (name is None or name == '') or float(row['G']) <= 0.0):
            # or not row['POS']):
            continue

        norm_name = name_normalizer(name)
        pos = []
        status = ""

        if 'POS' in row:
            # pos = row['POS'].decode('utf-8')
            pos = row['POS']
        pitcher['isFA'] = False
        pitcher['keeper'] = 0.0
        pitcher['name'] = name
        pitcher['normalized_first_name'] = norm_name['First']
        pitcher['last_name'] = norm_name['Last']
        # pitcher['team'] = (team_normalizer(row['Team'].decode('utf-8'))
        #                    if row['Team'] else "FA")
        pitcher['team'] = (team_normalizer(row['Team'])
                           if row['Team'] else "FA")
        pitcher['is_sp'] = True if 'SP' in pos else False
        pitcher['pos'] = pos
        pitcher['status'] = status
        pitcher['category'] = "pitcher"
        ip = float(row['IP'])
        pitcher['ip'] = ip
        w = float(row['W'])
        pitcher['w'] = w
        pitcher['g'] = float(row['G'])
        pitcher['sv'] = float(row['SV'])
        if 'SO' in row:
            k = float(row['SO'])
        else:
            k = float(row['K'])
        pitcher['k'] = k
        pitcher['kip'] = k / ip
        pitcher['winsip'] = w / ip
        pitcher['era'] = float(row['ERA'])
        pitcher['whip'] = float(row['WHIP'])
        # for cat in questionable_float_cats:
        #     if cat in row:
        #         pitcher[cat] = float(row[cat])
        # for cat in questionable_string_cats:
        #     if cat in row:
        #         pitcher[cat] = str(row[cat])
        pitcher_dict_list.append(pitcher)
    return pitcher_dict_list
