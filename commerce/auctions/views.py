from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import ListingForm
from .models import User, AuctionListing, Bid
from decimal import Decimal


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
        current_highest_bid = listing.bids.order_by('-amount').first()

        is_in_watchlist = request.user.is_authenticated and listing in request.user.watchlist.all() # If usuario logueado and existe lista 
        return render(request, "auctions/listing_detail.html", { # Return llevar a página de detalles del producto
            "listing": listing,
            "is_in_watchlist": is_in_watchlist,
            "current_highest_bid": current_highest_bid.amount if current_highest_bid else listing.starting_bid,
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
    listing = get_object_or_404(AuctionListing, id=listing_id) # Obtenemos el objeto de listado (listing) usando el listing_id. Si el listado no existe, se muestra un error 404.

    if request.method == "POST":
        new_bid_amount = Decimal(request.POST["new_bid"])  # Obtenemos el monto de la nueva oferta que el usuario introdujo en el formulario.
        current_highest_bid = listing.bids.order_by('-amount').first() # Si hay ofertas existentes, se ordenan por el monto de manera descendente y se toma la más alta.

        if new_bid_amount < listing.starting_bid: # Comparar con la Oferta Inicial
            messages.error(request, "Your bid must be at least as large as the starting bid.")

        elif current_highest_bid and new_bid_amount <= current_highest_bid.amount: # Comparar con la Oferta más Alta
            messages.error(request, "Your bid must be greater than the current highest bid.")

        else:
            new_bid = Bid(bidder=request.user, listing=listing, amount=new_bid_amount) # Guardar la Nueva Oferta
            new_bid.save()
            messages.success(request, "Your bid has been placed successfully!")

        return redirect("auctions:listing_detail", listing_id=listing_id)
    

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)

    if request.user == listing.owner and listing.is_active:
        highest_bid = listing.bids.order_by("-amount").first()

        if highest_bid:
            listing.winner = highest_bid.bidder
            listing.winning_bid = highest_bid.amount
        listing.is_active = False
        listing.save()

        return redirect('auctions:listing_detail', listing_id=listing_id)
    
    return redirect('auctions:index')