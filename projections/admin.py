from django.contrib import admin

from .models import BatterProjection, BatterValue, PitcherProjection, PitcherValue

# Register your models here.

admin.site.register(BatterProjection)
admin.site.register(BatterValue)
admin.site.register(PitcherProjection)
admin.site.register(PitcherValue)
