from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messages'  # keep as 'messages' for import, but use a different label
    label = 'user_messages'  # unique label for the app
