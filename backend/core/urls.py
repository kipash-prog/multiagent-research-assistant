from django.urls import path
from .views import QueryView, QueryListView, QueryDetailView

urlpatterns = [
    path("query/", QueryView.as_view(), name="create-query"),
    path("query/list/", QueryListView.as_view(), name="list-queries"),
    path("query/<int:pk>/", QueryDetailView.as_view(), name="query-detail"),
]
