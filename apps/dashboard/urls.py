from django.urls import path
from .views import dashboard, chatbot_query

urlpatterns = [

    path('', dashboard, name="dashboard"),
    path('chatbot/query/', chatbot_query, name='chatbot-query'),

]