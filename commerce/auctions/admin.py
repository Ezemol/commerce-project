from django.contrib import admin
from .models import AuctionListing, Comment, Bid

# Registra los modelos en la administración de Django
admin.site.register(AuctionListing)
admin.site.register(Comment)
admin.site.register(Bid)