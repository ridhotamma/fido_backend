from django.urls import path
from .views import MessageListView, MessageSendView

urlpatterns = [
    path('', MessageListView.as_view(), name='message-list'),
    path('send/<int:user_id>/', MessageSendView.as_view(), name='message-send'),
    path('with/<int:user_id>/', MessageListView.as_view(), name='message-thread'),
]
