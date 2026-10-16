
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def safety_score(request):
    lighting = 80
    open_shops = 70
    crowd_level = 60
    recent_reports = 90

    score = round(
        lighting * 0.30
        + open_shops * 0.25
        + crowd_level * 0.20
        + recent_reports * 0.25
    )

    return Response({
        "safety_score": score,
        "factors": {
            "lighting": lighting,
            "open_shops": open_shops,
            "crowd_level": crowd_level,
            "recent_reports": recent_reports
        },
        "message": "Illustrative score for development; not verified safety data."
    })

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home(request):
    return render(request, "safety/home.html")


@api_view(["GET"])
def safety_score(request):
    lighting = 80
    open_shops = 70
    crowd_level = 60
    recent_reports = 90

    score = round(
        lighting * 0.30
        + open_shops * 0.25
        + crowd_level * 0.20
        + recent_reports * 0.25
    )

    return Response({
        "safety_score": score,
        "factors": {
            "lighting": lighting,
            "open_shops": open_shops,
            "crowd_level": crowd_level,
            "recent_reports": recent_reports,
        },
        "message": "Illustrative score only; not verified safety data."
    })
