from django.apps import AppConfig


class IcerikConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'icerik'

    def ready(self):
        # Oturum olaylarını denetim kaydına bağlar (Paket F madde 9).
        from .denetim_kaydi import sinyalleri_bagla
        sinyalleri_bagla()
