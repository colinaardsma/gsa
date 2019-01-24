from django.test import TestCase
import django
import os
from datetime import datetime

# Create your tests here.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gsa.settings")
django.setup()
import projections.helpers.team_tools


def main():
    print(datetime.now().year - 1)
    # pitchers = projections.helpers.team_tools.create_full_pitcher_html("https://www.fantasypros.com/mlb/projections/pitchers.php")
    # print(pitchers)
    # batters = projections.helpers.team_tools.create_full_batter_html("https://www.fantasypros.com/mlb/projections/hitters.php")
    # print(batters)


main()
