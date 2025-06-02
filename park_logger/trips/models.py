from django.db import models

class Park(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    has_public_bathrooms = models.BooleanField(default=False)
    has_playground = models.BooleanField(default=False)
    has_basketball_court = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Trip(models.Model):
    park = models.ForeignKey(Park, on_delete=models.CASCADE, related_name='trips')
    visit_date = models.DateField()
    rating = models.IntegerField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='trip_images/', blank=True, null=True)

    def __str__(self):
        return f"Trip to {self.park.name} on {self.visit_date}"
