from django.apps import AppConfig


class IcerikConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'icerik'

    def ready(self):
        # Önbellek geçersizleştirme ve yavaş sorgu günlüğü (19 Ekim 2026,
        # başarım paketi). İkisi de içe aktarma anında değil burada bağlanır:
        # modeller ancak uygulama hazır olunca kullanılabilir.
        from . import sinyaller, yavas_sorgu
        sinyaller.bagla()
        yavas_sorgu.bagla()
        # Oturum olaylarını denetim kaydına bağlar (Paket F madde 9).
        from .denetim_kaydi import sinyalleri_bagla
        sinyalleri_bagla()
        # Oturum süresi için giriş damgası (Paket F madde 8).
        from .giris_guvenligi import sinyali_bagla
        sinyali_bagla()
        # Ayara bağlı sistem denetimleri (Paket L2): içe aktarma kaydeder.
        from cekirdek import denetimler  # noqa: F401

        # Arama metni haberle birlikte tazelenir (icerik/arama.py). Kanca
        # `Haber.save()` içinde değil burada: model dosyası arama motorunu
        # tanımasın, kanca tek yerden açılıp kapansın.
        from django.db.models.signals import post_save

        from . import arama
        from .models import Haber
        post_save.connect(arama.haber_kaydedildi, sender=Haber,
                          dispatch_uid="icerik.arama.haber_kaydedildi")
