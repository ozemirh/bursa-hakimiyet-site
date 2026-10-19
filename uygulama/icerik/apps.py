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
