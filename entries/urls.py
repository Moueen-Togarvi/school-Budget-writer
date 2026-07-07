from django.urls import path
from .views import DashboardView, EntryListView, EntryCreateView, EntryUpdateView, EntryDeleteView, ExportPDFView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('entries/', EntryListView.as_view(), name='entry_list'),
    path('entries/add/', EntryCreateView.as_view(), name='entry_create'),
    path('entries/<int:pk>/edit/', EntryUpdateView.as_view(), name='entry_update'),
    path('entries/<int:pk>/delete/', EntryDeleteView.as_view(), name='entry_delete'),
    path('entries/pdf/', ExportPDFView.as_view(), name='entry_pdf'),
]
