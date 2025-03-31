from django.contrib import admin

from revenue.models import Revenue


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    pass

