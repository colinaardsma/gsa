from django.contrib import admin

from .models import League, Profile


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['league_name', 'league_key', 'prev_year_league', 'prev_year_key', 'team_count', 'max_ip',
                       'season', 'batting_pos', 'pitcher_pos', 'bench_pos', 'dl_pos', 'na_pos', 'draft_status',
                       'start_date', 'end_date']}),
        ('Advanced Stats', {
            'fields': ['total_money_spent', 'money_spent_on_batters', 'money_spent_on_pitchers', 'batter_budget_pct',
                       'pitcher_budget_pct', 'batters_over_zero_dollars', 'pitchers_over_zero_dollars',
                       'one_dollar_batters', 'one_dollar_pitchers', 'b_dollar_per_fvaaz', 'p_dollar_per_fvaaz',
                       'b_player_pool_mult', 'p_player_pool_mult'], 'classes':['collapse']}),
        ('Advanced Stats Average', {
            'fields': ['total_money_spent_avg', 'money_spent_on_batters_avg', 'money_spent_on_pitchers_avg',
                       'batter_budget_pct_avg', 'pitcher_budget_pct_avg', 'batters_over_zero_dollars_avg',
                       'pitchers_over_zero_dollars_avg', 'one_dollar_batters_avg', 'one_dollar_pitchers_avg',
                       'b_dollar_per_fvaaz_avg', 'p_dollar_per_fvaaz_avg', 'b_player_pool_mult_avg',
                       'p_player_pool_mult_avg', ], 'classes': ['collapse']}),
        ('SGP', {
         'fields': ['r_sgp', 'hr_sgp', 'rbi_sgp', 'sb_sgp', 'ops_sgp', 'avg_sgp', 'w_sgp', 'sv_sgp', 'k_sgp',
                    'era_sgp', 'whip_sgp'], 'classes':['collapse']}),
        ('SGP Average', {
            'fields': ['r_sgp_avg', 'hr_sgp_avg', 'rbi_sgp_avg', 'sb_sgp_avg', 'ops_sgp_avg', 'avg_sgp_avg',
                       'w_sgp_avg', 'sv_sgp_avg', 'k_sgp_avg', 'era_sgp_avg', 'whip_sgp_avg', ],
            'classes': ['collapse']}),
        ('Users', {'fields': ['users'], 'classes': ['collapse']}),
    ]
    list_display = ('league_name', 'season', 'draft_status', 'league_key', 'prev_year_league', 'prev_year_key')
    list_filter = ['season']
    search_fields = ['league_name']

    def get_ordering(self, request):
        return ['-season']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['user', 'leagues', 'main_league', 'location']}),
        ('Yahoo!', {
            'fields': ['yahoo_guid', 'access_token', 'token_expiration', 'refresh_token', ], 'classes': ['collapse']}),
    ]
    list_display = ('user', 'main_league')
    list_filter = ['leagues', 'main_league']
    search_fields = ['user']

    def get_ordering(self, request):
        return ['-token_expiration']
