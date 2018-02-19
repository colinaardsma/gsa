from django.contrib import admin

from .models import BatterProjection, BatterValue, PitcherProjection, PitcherValue


@admin.register(BatterProjection)
class BatterProjectionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'status', 'last_modified',
                       'category', 'isFA']}),
        ('Raw Stats', {
            'fields': ['ab', 'r', 'hr', 'rbi', 'sb', 'avg', 'ops', ]}),
        ('Values', {
            'fields': ['dollarValue', 'fvaaz', 'keeper', ]}),
        ('Initial zScores', {
            'fields': ['zScoreR', 'zScoreHr', 'zScoreRbi', 'zScoreSb', 'zScoreAvg', 'zScoreOps', ],
            'classes': ['collapse']}),
        ('Weighted (Multiplied by AB) Stats', {
            'fields': ['weightedR', 'weightedHr', 'weightedRbi', 'weightedSb', 'weightedAvg', 'weightedOps', ],
            'classes': ['collapse']}),
        ('Weighted zScores', {
            'fields': ['weightedZscoreR', 'weightedZscoreHr', 'weightedZscoreRbi', 'weightedZscoreSb',
                       'weightedZscoreAvg', 'weightedZscoreOps', ], 'classes': ['collapse']}),
    ]
    list_display = ('name', 'team', 'pos', 'status', 'dollarValue', 'fvaaz', 'ab', 'r', 'hr', 'rbi', 'sb', 'avg', 'ops')
    list_filter = ['team', 'pos']
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['-fvaaz']


@admin.register(PitcherProjection)
class PitcherProjectionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'status', 'last_modified',
                       'category', 'is_sp', 'isFA']}),
        ('Raw Stats', {
            'fields': ['ip', 'w', 'sv', 'k', 'era', 'whip', 'kip', 'winsip', ], 'classes': ['collapse']}),
        ('Values', {
            'fields': ['dollarValue', 'fvaaz', 'keeper', ]}),
        ('Initial zScores', {
            'fields': ['zScoreW', 'zScoreSv', 'zScoreK', 'zScoreEra', 'zScoreWhip', ], 'classes': ['collapse']}),
        ('Weighted (Multiplied by AB) Stats', {
            'fields': ['weightedW', 'weightedSv', 'weightedK', 'weightedEra', 'weightedWhip', ],
            'classes': ['collapse']}),
        ('Weighted zScores', {
            'fields': ['weightedZscoreW', 'weightedZscoreSv', 'weightedZscoreK', 'weightedZscoreEra',
                       'weightedZscoreWhip', ], 'classes': ['collapse']}),
    ]
    list_display = ('name', 'team', 'pos', 'status', 'dollarValue', 'fvaaz', 'ip', 'w', 'sv', 'k', 'era', 'whip', 'kip',
                    'winsip')
    list_filter = ['team', 'pos']
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['-fvaaz']


@admin.register(BatterValue)
class BatterValueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Foreign Keys', {
            'fields': ['batter', 'league', 'user', 'yahoo_guid']}),
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'last_modified',
                       'category', 'isFA']}),
        ('Values', {
            'fields': ['dollarValue', 'fvaaz', 'keeper', ]}),
        ('Initial zScores', {
            'fields': ['zScoreR', 'zScoreHr', 'zScoreRbi', 'zScoreSb', 'zScoreAvg', 'zScoreOps', ],
            'classes': ['collapse']}),
        ('Weighted (Multiplied by AB) Stats', {
            'fields': ['weightedR', 'weightedHr', 'weightedRbi', 'weightedSb', 'weightedAvg', 'weightedOps', ],
            'classes': ['collapse']}),
        ('Weighted zScores', {
            'fields': ['weightedZscoreR', 'weightedZscoreHr', 'weightedZscoreRbi', 'weightedZscoreSb',
                       'weightedZscoreAvg', 'weightedZscoreOps', ], 'classes': ['collapse']}),
    ]
    list_display = ('name', 'team', 'pos', 'dollarValue', 'fvaaz')
    list_filter = ['team', 'pos']
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['user', 'league', '-fvaaz']


@admin.register(PitcherValue)
class PitcherValueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'last_modified',
                       'category', 'is_sp', 'isFA']}),
        ('Values', {
            'fields': ['dollarValue', 'fvaaz', 'keeper', ]}),
        ('Initial zScores', {
            'fields': ['zScoreW', 'zScoreSv', 'zScoreK', 'zScoreEra', 'zScoreWhip', ], 'classes': ['collapse']}),
        ('Weighted (Multiplied by AB) Stats', {
            'fields': ['weightedW', 'weightedSv', 'weightedK', 'weightedEra', 'weightedWhip', ],
            'classes': ['collapse']}),
        ('Weighted zScores', {
            'fields': ['weightedZscoreW', 'weightedZscoreSv', 'weightedZscoreK', 'weightedZscoreEra',
                       'weightedZscoreWhip', ], 'classes': ['collapse']}),
    ]
    list_display = ('name', 'team', 'pos', 'dollarValue', 'fvaaz')
    list_filter = ['team', 'pos']
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['user', 'league', '-fvaaz']
