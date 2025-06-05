from django.contrib import admin

from .models import CustomUser, Follow, CoinClaimHistory

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Follow)
admin.site.register(CoinClaimHistory)
