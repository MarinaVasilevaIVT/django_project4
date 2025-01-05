from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

app_name = "polls"

urlpatterns = [
    # Главная страница с опросами
    path("", views.IndexView.as_view(), name="index"),
    # Страница с деталями опроса
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # Страница с результатами опроса
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # Страница для голосования
    path("<int:question_id>/vote/", views.vote, name="vote"),
    # Страница для создания нового опроса
    path("create/", views.create_poll, name="create_poll"),
    
    # Маршруты для аутентификации
    path("login/", LoginView.as_view(template_name="polls/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),

    # Маршруты для статистики
    path("statistics", views.StatisticsView.as_view(), name="statistics"),
    path("statistics-question-list", views.QuestionView.as_view(), name="statistics-question-list"),
    path('statistics/question-stats/<int:pk>/', views.QuestionStatsAPIView.as_view(), name='statistics-question-stats'),
    path('export/', views.ExportDataView.as_view(), name='export_data'),
]
