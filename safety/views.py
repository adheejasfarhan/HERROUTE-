
import json
import math
import urllib.error
import urllib.parse
import urllib.request

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import SafetyIncident


def home(request):
    return render(request, "safety/home.html")


def distance_meters(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in metres."""
    earth_radius = 6371000

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

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(max(0, 1 - a))
    )

    return earth_radius * c


def calculate_route_safety(route_coordinates, route_number=1):
    """Calculate a route score using nearby incident reports."""

    now = timezone.now()
    incidents = SafetyIncident.objects.all()

    total_risk = 0
    incidents_on_route = 0

    for incident in incidents:
        minimum_distance = float("inf")

        for point in route_coordinates:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            lon, lat = point[0], point[1]

            distance = distance_meters(
                lat, lon,
                incident.latitude, incident.longitude
            )
            minimum_distance = min(minimum_distance, distance)

        if minimum_distance <= 300:
            incidents_on_route += 1

            age_hours = max(
                0,
                (now - incident.created_at).total_seconds() / 3600
            )
            decay = math.exp(-age_hours / 12)
            distance_factor = 1 - minimum_distance / 300

            total_risk += (
                incident.severity
                * 15
                * decay
                * distance_factor
            )

    # These are demo values, not live measurements.
    lighting_score = 75
    establishments_score = 85
    crowd_score = 60

    if incidents_on_route == 0:
        return {
            "score": None,
            "status": "Unreported",
            "is_unreported": True,
            "incidents_found": 0,
            "lighting": None,
            "establishments": None,
            "crowd": None,
            "recent_reports": None,
        }

    report_safety = max(20, min(100, 100 - total_risk))

    final_score = (
        lighting_score * 0.20
        + establishments_score * 0.30
        + crowd_score * 0.15
        + report_safety * 0.35
    )

    return {
        "score": round(final_score),
        "status": "Scored",
        "is_unreported": False,
        "incidents_found": incidents_on_route,
        "lighting": lighting_score,
        "establishments": establishments_score,
        "crowd": crowd_score,
        "recent_reports": round(report_safety),
    }


@csrf_exempt
def safety_score_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"}, status=405
        )

    try:
        data = json.loads(request.body)
        coordinates = data.get("coordinates", [])

        if not isinstance(coordinates, list) or not coordinates:
            return JsonResponse(
                {"error": "Route coordinates are required"},
                status=400
            )

        result = calculate_route_safety(coordinates)
        return JsonResponse(result)

    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Invalid request data"}, status=400
        )


@csrf_exempt
def route_incidents_api(request):
    """Return incident reports within 300 metres of a route."""

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"}, status=405
        )

    try:
        data = json.loads(request.body)
        coordinates = data.get("coordinates", [])

        if not isinstance(coordinates, list) or not coordinates:
            return JsonResponse({"incidents": []})

        nearby_incidents = []
        now = timezone.now()

        for incident in SafetyIncident.objects.all():
            minimum_distance = float("inf")

            for point in coordinates:
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    continue

                lon, lat = point[0], point[1]
                distance = distance_meters(
                    lat, lon,
                    incident.latitude, incident.longitude
                )
                minimum_distance = min(minimum_distance, distance)

            if minimum_distance <= 300:
                age_hours = max(
                    0,
                    (now - incident.created_at).total_seconds() / 3600
                )

                nearby_incidents.append({
                    "latitude": incident.latitude,
                    "longitude": incident.longitude,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "description": incident.description,
                    "distance": round(minimum_distance),
                    "age_hours": round(age_hours, 1),
                })

        return JsonResponse({"incidents": nearby_incidents})

    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Invalid request data"}, status=400
        )


@csrf_exempt
def report_incident_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"}, status=405
        )

    try:
        data = json.loads(request.body)

        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
        incident_type = data.get("incident_type", "unsafe")
        severity = int(data.get("severity", 2))
        description = data.get("description", "")

        valid_types = {
            "poor_lighting", "unsafe", "harassment",
            "suspicious", "crowd", "other"
        }

        if not (-90 <= latitude <= 90):
            return JsonResponse(
                {"error": "Invalid latitude"}, status=400
            )

        if not (-180 <= longitude <= 180):
            return JsonResponse(
                {"error": "Invalid longitude"}, status=400
            )

        if incident_type not in valid_types:
            return JsonResponse(
                {"error": "Invalid incident type"}, status=400
            )

        if severity not in (1, 2, 3):
            return JsonResponse(
                {"error": "Invalid severity"}, status=400
            )

        if not isinstance(description, str) or len(description) > 1000:
            return JsonResponse(
                {"error": "Description must be 1000 characters or fewer"},
                status=400
            )

        incident = SafetyIncident.objects.create(
            latitude=latitude,
            longitude=longitude,
            incident_type=incident_type,
            severity=severity,
            description=description
        )

        return JsonResponse({
            "success": True,
            "message": "Incident report submitted",
            "incident": {
                "id": incident.id,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "description": incident.description,
            }
        })

    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Invalid request data"}, status=400
        )


@require_GET
def all_incidents_api(request):
    """Return incident reports. Add moderation before public production use."""

    incidents = SafetyIncident.objects.all().order_by("-created_at")
    now = timezone.now()

    incident_list = []

    for incident in incidents:
        age_hours = max(
            0,
            (now - incident.created_at).total_seconds() / 3600
        )

        incident_list.append({
            "id": incident.id,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "description": incident.description,
            "age_hours": round(age_hours, 1),
        })

    return JsonResponse({"incidents": incident_list})

@require_GET
def nearby_places_api(request):
    """
    Return mapped support places around a coordinate.
    Opening hours may be unknown and are not independently verified.
    """

    try:
        latitude = float(request.GET.get("lat", ""))
        longitude = float(request.GET.get("lon", ""))
        radius = int(request.GET.get("radius", "1000"))

        if not -90 <= latitude <= 90:
            return JsonResponse(
                {"error": "Invalid latitude"},
                status=400
            )

        if not -180 <= longitude <= 180:
            return JsonResponse(
                {"error": "Invalid longitude"},
                status=400
            )

        if not 200 <= radius <= 2000:
            return JsonResponse(
                {"error": "Radius must be between 200 and 2000 metres"},
                status=400
            )

    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Please provide valid coordinates and radius"},
            status=400
        )

    cache_key = (
        f"herroute_support_v3_{latitude:.4f}_"
        f"{longitude:.4f}_{radius}"
    )

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return JsonResponse(cached_result)

    query = f"""
    [out:json][timeout:15];
    (
      node(around:{radius},{latitude},{longitude})
        ["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station|toilets)$"];
      way(around:{radius},{latitude},{longitude})
        ["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station|toilets)$"];
      relation(around:{radius},{latitude},{longitude})
        ["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station|toilets)$"];
    );
    out center tags;
    """

    body = urllib.parse.urlencode(
        {"data": query}
    ).encode("utf-8")

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    raw_data = None
    last_error = None

    for endpoint in endpoints:
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "User-Agent": "HerRoutePrototype/1.0",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=18) as response:
                raw_data = json.loads(
                    response.read().decode("utf-8")
                )
            break

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as error:
            last_error = error
            print(
                f"Overpass endpoint failed ({endpoint}): "
                f"{repr(error)}"
            )

    if raw_data is None:
        print("All Overpass endpoints failed:", repr(last_error))

        # Briefly cache the failure to prevent repeated requests
        # from repeatedly hitting unavailable external servers.
        cache.set(
            cache_key + "_unavailable",
            True,
            30
        )

        return JsonResponse(
            {
                "error": "Support-place service is temporarily unavailable",
                "places": []
            },
            status=502
        )

    places = []
    seen = set()

    for element in raw_data.get("elements", []):
        tags = element.get("tags", {})

        lat = element.get("lat")
        lon = element.get("lon")

        if lat is None or lon is None:
            center = element.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

        if lat is None or lon is None:
            continue

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            continue

        place_id = f'{element.get("type")}-{element.get("id")}'

        if place_id in seen:
            continue
        seen.add(place_id)

        category = tags.get("amenity", "support")
        opening_hours = tags.get("opening_hours", "").strip()
        name = tags.get("name") or (
            f"Unnamed {category.replace('_', ' ')}"
        )

        places.append({
            "id": place_id,
            "name": name,
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "opening_hours": opening_hours or "Hours not listed",
            "is_listed_24_7": opening_hours == "24/7",
            "source": "OpenStreetMap",
            "verification": "Not independently verified",
        })

    result = {"places": places}

    # Cache successful results, including empty results.
    cache.set(cache_key, result, 300)

    return JsonResponse(result)

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import SafetyIncident


@require_POST
@csrf_protect
def report_incident(request):
    try:
        data = json.loads(request.body)

        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        incident_type = data["incident_type"]
        severity = int(data["severity"])
        description = data.get("description", "").strip()

        valid_types = dict(SafetyIncident.INCIDENT_TYPES)

        if incident_type not in valid_types:
            return JsonResponse(
                {"error": "Invalid incident type."},
                status=400
            )

        if severity not in dict(SafetyIncident.SEVERITY_LEVELS):
            return JsonResponse(
                {"error": "Invalid severity."},
                status=400
            )

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return JsonResponse(
                {"error": "Invalid location coordinates."},
                status=400
            )

        incident = SafetyIncident.objects.create(
            latitude=latitude,
            longitude=longitude,
            incident_type=incident_type,
            severity=severity,
            description=description
        )

        return JsonResponse({
            "success": True,
            "message": "Safety report saved successfully.",
            "incident": {
                "id": incident.id,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "description": incident.description,
                "created_at": incident.created_at.isoformat()
            }
        }, status=201)

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Invalid report data. Please check the form values."},
            status=400
        )
