from django.apps import AppConfig


class IcerikConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'icerik'

    def ready(self):
        # Arama metni haberle birlikte tazelenir (icerik/arama.py). Kanca
        # `Haber.save()` içinde değil burada: model dosyası arama motorunu
        # tanımasın, kanca tek yerden açılıp kapansın.
        from django.db.models.signals import post_save

        from . import arama
        from .models import Haber
        post_save.connect(arama.haber_kaydedildi, sender=Haber,
                          dispatch_uid="icerik.arama.haber_kaydedildi")
