from django.contrib import admin

from desk.models import Bale, Contract, HVIReport, PriceIndex


@admin.register(Bale)
class BaleAdmin(admin.ModelAdmin):
    list_display = ("code", "season", "producer", "weight_kg", "classification_date")
    list_filter = ("season",)
    search_fields = ("code", "producer")
    date_hierarchy = "classification_date"


@admin.register(HVIReport)
class HVIReportAdmin(admin.ModelAdmin):
    list_display = ("bale", "micronaire", "length", "strength", "uniformity")
    search_fields = ("bale__code",)
    list_select_related = ("bale",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("bale", "buyer", "price_per_kg", "closing_date")
    search_fields = ("bale__code", "buyer")
    list_select_related = ("bale",)


@admin.register(PriceIndex)
class PriceIndexAdmin(admin.ModelAdmin):
    list_display = ("code", "value", "trading_date")
    list_filter = ("code",)
    date_hierarchy = "trading_date"
