from django.apps import AppConfig

class ITIHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ITIHub'

    def ready(self):
        import ITIHub.models
