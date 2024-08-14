from django.db import models
from django.contrib.auth.models import User, AbstractUser

# Model para usuario
class User(AbstractUser):
    watchlist = models.ManyToManyField('AuctionListing', blank=True, related_name='watchlisted_by')

class AuctionListing(models.Model):
    CATEGORY_CHOICES = [
        ('SPORTS', 'Sports'),
        ('ELECTRONICS', 'Electronics'),
        ('FASHION', 'Fashion'),
        ('HOME', 'Home'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title



# Model para ofertas
class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} - {self.amount}"


# Model para comentarios realizados en listados de subastas.
class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()

    def __str__(self):
        return f"Comment by {self.commenter.username} on {self.listing.title}"