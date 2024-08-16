from django.urls import path

from . import views

app_name = 'auctions'

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("watchlist/<int:listing_id>/", views.watchlist, name="watchlist"),
    path("bid/<int:listing_id>/", views.bid, name="bid"),
    path("close_auction/<int:listing_id>/", views.close_auction, name="close_auction"),
    path("comment/<int:listing_id>/", views.comment, name="comment"),
    path("watchlist_store", views.watchlist_store, name="watchlist_store"),
    path("categories/", views.categories, name="categories"),
    path("categories/<str:category_name>/", views.category_listings, name="category_listings"),
]

    