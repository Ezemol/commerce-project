from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import ListingForm
from .models import User, AuctionListing, Bid, Comment
from decimal import Decimal

# Vista para la página principal que muestra las subastas activas.
def index(request):
    # Obtén todas las subastas activas
    active_listings = AuctionListing.objects.filter(is_active=True)

    # Si el usuario está autenticado, también obtén las subastas ganadas por el usuario
    if request.user.is_authenticated:
        won_listings = AuctionListing.objects.filter(winner=request.user)
    else:
        won_listings = []

    return render(request, "auctions/index.html", {
        "active_listings": active_listings,
        "won_listings": won_listings,
    })
# Vista para iniciar sesión en la aplicación.
def login_view(request):
    if request.method == "POST":
        # Intentar autenticar al usuario
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Verificar si la autenticación fue exitosa
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

# Vista para cerrar sesión en la aplicación.
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))

# Vista para registrar un nuevo usuario.
def register(request):
    if request.method == "POST" and request.method is not None:
        username = request.POST["username"]
        email = request.POST["email"]

        # Verificar que las contraseñas coincidan.
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Intentar crear un nuevo usuario.
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

# Vista para crear una nueva subasta.
@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)  # Formulario de subasta creado por el usuario.
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user  # Asigna al usuario actual como propietario.
            listing.is_active = True  # Marca la subasta como activa.
            listing.save()
            return redirect("auctions:index")
    else:
        form = ListingForm()  # Inicializa el formulario para solicitudes GET.

    return render(request, "auctions/create_listing.html", {
        "form": form
    })

# Vista para mostrar los detalles de una subasta específica.
def listing_detail(request, listing_id):
    if request.method == "GET":
        listing = get_object_or_404(AuctionListing, id=listing_id)  # Obtener la subasta o mostrar error 404 si no existe.
        current_highest_bid = listing.bids.order_by('-amount').first()  # Obtener la oferta más alta.
        is_in_watchlist = request.user.is_authenticated and listing in request.user.watchlist.all()  # Verifica si está en la lista de seguimiento del usuario.

        # Obtener todos los comentarios asociados a la subasta.
        comments = Comment.objects.filter(listing=listing)

        return render(request, "auctions/listing_detail.html", {
            "listing": listing,
            "is_in_watchlist": is_in_watchlist,
            "current_highest_bid": current_highest_bid.amount if current_highest_bid else listing.starting_bid,
            "comments": comments  # Pasa los comentarios como queryset.
        })

# Vista para agregar o remover una subasta a/de la lista de seguimiento del usuario.
@login_required
def watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)  # Obtener la subasta o mostrar error 404 si no existe.

    if listing in request.user.watchlist.all():
        request.user.watchlist.remove(listing)  # Remover de la lista de seguimiento si ya está añadida.
    else:
        request.user.watchlist.add(listing)  # Agregar a la lista de seguimiento si no está añadida.

    return redirect('auctions:listing_detail', listing_id=listing_id)

# Vista para realizar una oferta en una subasta.
@login_required
def bid(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)  # Obtener la subasta o mostrar error 404 si no existe.

    if request.method == "POST":
        new_bid_amount = Decimal(request.POST["new_bid"])  # Obtener el monto de la nueva oferta.
        current_highest_bid = listing.bids.order_by('-amount').first()  # Obtener la oferta más alta si existe.

        if new_bid_amount < listing.starting_bid:  # Verificar que la oferta sea mayor o igual a la oferta inicial.
            messages.error(request, "Your bid must be at least as large as the starting bid.")

        elif current_highest_bid and new_bid_amount <= current_highest_bid.amount:  # Verificar que la oferta sea mayor a la oferta más alta.
            messages.error(request, "Your bid must be greater than the current highest bid.")

        else:
            new_bid = Bid(bidder=request.user, listing=listing, amount=new_bid_amount)  # Crear y guardar la nueva oferta.
            new_bid.save()
            messages.success(request, "Your bid has been placed successfully!")

        return redirect("auctions:listing_detail", listing_id=listing_id)

# Vista para cerrar una subasta.
@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)  # Obtener la subasta o mostrar error 404 si no existe.

    if request.user == listing.owner and listing.is_active:  # Verificar que el usuario actual sea el propietario y la subasta esté activa.
        highest_bid = listing.bids.order_by("-amount").first()  # Obtener la oferta más alta.

        if highest_bid:
            listing.winner = highest_bid.bidder  # Asignar el ganador como el usuario con la oferta más alta.
            listing.winning_bid = highest_bid.amount  # Asignar la oferta ganadora.
        listing.is_active = False  # Marcar la subasta como inactiva.
        listing.save()

        return redirect('auctions:listing_detail', listing_id=listing_id)

    return redirect('auctions:index')

# Vista para agregar un comentario a una subasta.
@login_required
def comment(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)  # Obtener la subasta o mostrar error 404 si no existe.

    if request.method == "POST" and request.method is not None:
        new_comment = Comment(commenter=request.user, listing=listing, content=request.POST["comment"])  # Crear y guardar el nuevo comentario.
        new_comment.save()
    return redirect("auctions:listing_detail", listing_id=listing_id)

# Vista para mostrar todas las subastas en la lista de seguimiento del usuario.
@login_required
def watchlist_store(request):
    all_watchlists = request.user.watchlist.all()  # Obtener todas las subastas en la lista de seguimiento del usuario.

    return render(request, "auctions/watchlist.html", {
        "all_watchlists": all_watchlists,
    })

# Vista para mostrar todas las categorías disponibles.
def categories(request):
    categories = [choice[0] for choice in AuctionListing.CATEGORY_CHOICES]  # Obtener todas las categorías posibles.

    return render(request, "auctions/categories.html", {
        "categories": categories
    })

# Vista para mostrar todas las subastas activas en una categoría específica.
def category_listings(request, category_name):
    listings = AuctionListing.objects.filter(category=category_name, is_active=True)  # Filtrar las subastas activas por categoría.

    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": listings
    })
