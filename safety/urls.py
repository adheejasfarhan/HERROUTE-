from django.urls import path
from .import views

urlpatterns = [

    path('',views.home,name='home'),
    path("safety-score/", views.safety_score_api, name="safety_score_api"),
    path("route-incidents/",views.route_incidents_api,name="route_incidents_api"),
    path(
    "report-incident/",
    views.report_incident_api,
    name="report_incident_api"
),
    path(
    "incidents/",
    views.all_incidents_api,
    name="all_incidents_api"
),

path(
    "nearby-places/",
    views.nearby_places_api,
    name="nearby_places_api",
),

]