

from django.shortcuts import render,redirect,HttpResponse
from .import models
from datetime import datetime
# Create your views here.
import math
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

from .models import SafetyIncident
from django.shortcuts import render

def home(request):
    return render(request, 'safety/home.html')
import math
from django.http import JsonResponse
from django.utils import timezone

from .models import SafetyIncident
def distance_meters(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in meters."""

    R = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_route_safety(route_coordinates, route_number=1):
    """Calculate Safety score based strictly on reported data."""
    
    now = timezone.now()
    incidents = SafetyIncident.objects.all()

    total_risk = 0
    incidents_on_route = 0

    # Check every incident
    for incident in incidents:
        minimum_distance = float("inf")

        for point in route_coordinates:
            lon = point[0]
            lat = point[1]

            distance = distance_meters(
                lat, lon, incident.latitude, incident.longitude
            )
            minimum_distance = min(minimum_distance, distance)

        # Only incidents within 300 meters affect the route
        if minimum_distance <= 300:
            incidents_on_route += 1
            
            age_hours = (
                now - incident.created_at
            ).total_seconds() / 3600

            # New reports have stronger influence
            decay = math.exp(-age_hours / 12)

            # Closer reports have stronger influence
            distance_factor = (1 - (minimum_distance / 300))

            # Severity: 1 = low, 2 = medium, 3 = high
            risk = (
                incident.severity
                * 15
                * decay
                * distance_factor
            )

            total_risk += risk

    # If no incidents are nearby, mark as unreported
    if incidents_on_route == 0:
        return {
            "score": None,
            "status": "Unreported",
            "is_unreported": True,
            "incidents_found": 0
        }

    # Convert incident risk into a 0-100 report score
    score = max(20, min(100, 100 - total_risk))

    return {
        "score": round(score),
        "status": "Scored",
        "is_unreported": False,
        "incidents_found": incidents_on_route
    }
@csrf_exempt
def safety_score_api(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=405
        )

    try:
        import json

        data = json.loads(request.body)

        route_coordinates = data.get(
            "coordinates",
            []
        )

        route_number = int(
            data.get("route_number", 1)
        )

        result = calculate_route_safety(
            route_coordinates,
            route_number
        )

        return JsonResponse(result)

    except Exception as e:

        return JsonResponse(
            {"error": str(e)},
            status=400
        )
@csrf_exempt
def route_incidents_api(request):
    """
    Return safety incidents that are within 300 meters
    of the supplied route.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=405
        )

    try:
        import json

        data = json.loads(request.body)

        route_coordinates = data.get("coordinates", [])

        if not route_coordinates:
            return JsonResponse({
                "incidents": []
            })

        incidents = SafetyIncident.objects.all()

        nearby_incidents = []

        for incident in incidents:

            minimum_distance = float("inf")

            # Check distance from incident to route
            for point in route_coordinates:

                lon = point[0]
                lat = point[1]

                distance = distance_meters(
                    lat,
                    lon,
                    incident.latitude,
                    incident.longitude
                )

                minimum_distance = min(
                    minimum_distance,
                    distance
                )

            # Only incidents within 300 meters
            if minimum_distance <= 300:

                age_hours = (
                    timezone.now() - incident.created_at
                ).total_seconds() / 3600

                nearby_incidents.append({
                    "latitude": incident.latitude,
                    "longitude": incident.longitude,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "description": incident.description,
                    "distance": round(minimum_distance),
                    "age_hours": round(age_hours, 1),
                })

        return JsonResponse({
            "incidents": nearby_incidents
        })

    except Exception as e:

        return JsonResponse(
            {"error": str(e)},
            status=400
        )
@csrf_exempt
def report_incident_api(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=405
        )

    try:
        import json

        data = json.loads(request.body)

        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))

        incident_type = data.get(
            "incident_type",
            "unsafe"
        )

        severity = int(
            data.get("severity", 2)
        )

        description = data.get(
            "description",
            ""
        )

        # Validate incident type
        valid_types = [
            "poor_lighting",
            "unsafe",
            "harassment",
            "suspicious",
            "crowd",
            "other"
        ]

        if incident_type not in valid_types:
            return JsonResponse(
                {"error": "Invalid incident type"},
                status=400
            )

        # Validate severity
        if severity not in [1, 2, 3]:
            return JsonResponse(
                {"error": "Invalid severity"},
                status=400
            )

        # Create database record
        incident = SafetyIncident.objects.create(
            latitude=latitude,
            longitude=longitude,
            incident_type=incident_type,
            severity=severity,
            description=description
        )

        return JsonResponse({
            "success": True,
            "message": "Unsafe area reported successfully",

            "incident": {
                "id": incident.id,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "description": incident.description,
            }
        })

    except Exception as e:

        return JsonResponse(
            {"error": str(e)},
            status=400
        )
@csrf_exempt
def all_incidents_api(request):

    if request.method != "GET":
        return JsonResponse(
            {"error": "GET request required"},
            status=405
        )

    try:
        incidents = SafetyIncident.objects.all().order_by("-created_at")

        incident_list = []

        for incident in incidents:

            age_hours = (
                timezone.now() - incident.created_at
            ).total_seconds() / 3600

            incident_list.append({
                "id": incident.id,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "description": incident.description,
                "age_hours": round(age_hours, 1),
            })

        return JsonResponse({
            "incidents": incident_list
        })

    except Exception as e:

        return JsonResponse(
            {"error": str(e)},
            status=400
        )
        

import json
import urllib.parse
import urllib.request
import urllib.error

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def nearby_places_api(request):
    """Return mapped support places within a limited search area."""

    try:
        latitude = float(request.GET.get("lat", ""))
        longitude = float(request.GET.get("lon", ""))
        radius = int(request.GET.get("radius", "1000"))

        if not (-90 <= latitude <= 90):
            return JsonResponse(
                {"error": "Invalid latitude"}, status=400
            )

        if not (-180 <= longitude <= 180):
            return JsonResponse(
                {"error": "Invalid longitude"}, status=400
            )

        if not 200 <= radius <= 2000:
            return JsonResponse(
                {"error": "Radius must be between 200 and 2000 metres"},
                status=400
            )

        cache_key = (
            f"nearby_support_v1_{latitude:.4f}_"
            f"{longitude:.4f}_{radius}"
        )
        cached = cache.get(cache_key)

        if cached is not None:
            return JsonResponse(cached)

        query = f"""
        [out:json][timeout:15];
        (
          node(around:{radius},{latitude},{longitude})["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station)$"];
          way(around:{radius},{latitude},{longitude})["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station)$"];
          relation(around:{radius},{latitude},{longitude})["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station)$"];
        );
        out center tags;
        """

        endpoint = "https://overpass-api.de/api/interpreter"
        body = urllib.parse.urlencode({"data": query}).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "User-Agent": "HerRoutePrototype/1.0 (safety map)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            raw_data = json.loads(response.read().decode("utf-8"))

        places = []

        for element in raw_data.get("elements", []):
            tags = element.get("tags", {})

            # Nodes have direct coordinates; ways/relations usually have a center.
            lat = element.get("lat")
            lon = element.get("lon")

            if lat is None or lon is None:
                center = element.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            category = tags.get("amenity", "support")
            name = tags.get("name", "Unnamed support place")

            places.append({
                "id": f'{element.get("type")}-{element.get("id")}',
                "name": name,
                "category": category,
                "latitude": lat,
                "longitude": lon,
                "opening_hours": tags.get(
                    "opening_hours", "Hours not listed"
                ),
                "source": "OpenStreetMap",
                "verification": "Not independently verified",
            })

        result = {"places": places}
        cache.set(cache_key, result, 300)  # Cache for five minutes

        return JsonResponse(result)

    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Please provide valid coordinates and radius"},
            status=400
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Support-place service is temporarily unavailable"},
            status=502
        )
