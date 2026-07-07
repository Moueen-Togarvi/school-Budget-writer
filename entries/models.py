from django.db import models

class Entry(models.Model):
    name = models.CharField(max_length=200)
    money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.name
