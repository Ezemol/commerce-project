from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import ListingForm
from .models import User, AuctionListing


def index(request):
    listings = AuctionListing.objects.filter(is_active=True)
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)  # Form = subasta hecha por usuario
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.is_active = True
            listing.save()
            return redirect("auctions:index")
    else:
        form = ListingForm()  # Inicializa form para solicitudes GET

    return render(request, "auctions/create_listing.html", {
        "form": form
    })   


def listing_detail(request, listing_id):
    if request.method == "GET":
        listing = get_object_or_404(AuctionListing, id=listing_id)
        is_in_watchlist = request.user.is_authenticated and listing in request.user.watchlist.all() # If usuario logueado and existe lista 
        return render(request, "auctions/listing_detail.html", { # Return llevar a página de detalles del producto
            "listing": listing,
            "is_in_watchlist": is_in_watchlist
        })
    return render(request, "auctions/index.html")


@login_required
def watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)

    if listing in request.user.watchlist.all():
        request.user.watchlist.remove(listing)
    else:
        request.user.watchlist.add(listing)
    
    return redirect('auctions:listing_detail', listing_id=listing_id)

@login_required
def bid(request, listing_id):
    pass