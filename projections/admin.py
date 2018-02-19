from django.contrib import admin

from .models import BatterProjection, BatterValue, PitcherProjection, PitcherValue


class PosListFilter(admin.SimpleListFilter):
    """This is a list filter based on the values
    from a model's `keywords` ArrayField. """

    title = 'POS'
    parameter_name = 'pos'

    def lookups(self, request, model_admin):
        # Very similar to our code above, but this method must return a
        # list of tuples: (lookup_value, human-readable value). These
        # appear in the admin's right sidebar

        if isinstance(model_admin, BatterProjectionAdmin):
            positions = BatterProjection.objects.values_list("pos", flat=True)
            positions = [(pos, pos) for sublist in positions for pos in sublist if pos]
            positions = sorted(set(positions))
            return positions
        if isinstance(model_admin, BatterValueAdmin):
            positions = BatterValue.objects.values_list("pos", flat=True)
            positions = [(pos, pos) for sublist in positions for pos in sublist if pos]
            positions = sorted(set(positions))
            return positions
        if isinstance(model_admin, PitcherProjectionAdmin):
            positions = PitcherProjection.objects.values_list("pos", flat=True)
            positions = [(pos, pos) for sublist in positions for pos in sublist if pos]
            positions = sorted(set(positions))
            return positions
        if isinstance(model_admin, PitcherValueAdmin):
            positions = PitcherValue.objects.values_list("pos", flat=True)
            positions = [(pos, pos) for sublist in positions for pos in sublist if pos]
            positions = sorted(set(positions))
            return positions

    def queryset(self, request, queryset):
        # when a user clicks on a filter, this method gets called. The
        # provided queryset with be a queryset of Items, so we need to
        # filter that based on the clicked keyword.

        lookup_value = self.value()  # The clicked keyword. It can be None!
        if lookup_value:
            # the __contains lookup expects a list, so...
            queryset = queryset.filter(pos__contains=[lookup_value])
        return queryset


@admin.register(BatterProjection)
class BatterProjectionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'status', 'category', 'isFA']}),
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
    list_filter = ['team', PosListFilter, ]
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['-fvaaz']


@admin.register(PitcherProjection)
class PitcherProjectionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'status', 'category', 'is_sp', 'isFA']}),
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
    list_filter = ['team', PosListFilter, ]
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['-fvaaz']


@admin.register(BatterValue)
class BatterValueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Foreign Keys', {
            'fields': ['batter', 'league', 'user', 'yahoo_guid']}),
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'category', 'isFA']}),
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
    list_filter = ['team', PosListFilter, ]
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['user', 'league', '-fvaaz']


@admin.register(PitcherValue)
class PitcherValueAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Descriptive Properties', {
            'fields': ['name', 'normalized_first_name', 'last_name', 'team', 'pos', 'category', 'is_sp', 'isFA']}),
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
    list_filter = ['team', PosListFilter, ]
    search_fields = ['pos']

    def get_ordering(self, request):
        return ['user', 'league', '-fvaaz']
