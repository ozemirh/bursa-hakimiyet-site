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
