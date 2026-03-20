from django.urls import path

from .views import RoundDetailView, RoundListCreateView, TermDetailView, TermListCreateView

urlpatterns = [
    path("terms", TermListCreateView.as_view(), name="term_list_create"),
    path("terms/<int:term_id>", TermDetailView.as_view(), name="term_detail"),
    path("rounds", RoundListCreateView.as_view(), name="round_list_create"),
    path("rounds/<int:round_id>", RoundDetailView.as_view(), name="round_detail"),
]
