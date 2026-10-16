from django.db import models
from django.db import models


class SafetyIncident(models.Model):
    INCIDENT_TYPES = [
        ("poor_lighting", "Poor Lighting"),
        ("unsafe", "Unsafe Area"),
        ("harassment", "Harassment"),
        ("suspicious", "Suspicious Activity"),
        ("crowd", "Crowd Issue"),
        ("other", "Other"),
    ]

    SEVERITY_LEVELS = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
    ]

    latitude = models.FloatField()
    longitude = models.FloatField()

    incident_type = models.CharField(
        max_length=50,
        choices=INCIDENT_TYPES,
        default="unsafe"
    )

    severity = models.IntegerField(
        choices=SEVERITY_LEVELS,
        default=2
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.incident_type} - {self.latitude}, {self.longitude}"
# Create your models here.
