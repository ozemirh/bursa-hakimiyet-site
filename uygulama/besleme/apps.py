from django.apps import AppConfig


class BeslemeConfig(AppConfig):
    """Sitemap ve RSS uygulaması.

    Modeli yoktur; göçmen (migration) klasörü de yoktur. Yaptığı tek iş,
    başka uygulamaların kayıtlarını arama motorlarının beklediği XML
    dosyalarına çevirmektir.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "besleme"
    verbose_name = "besleme"

    def ready(self):
        # Aile kayıt defteri burada dolar. `kaynaklar` içe aktarıldığı anda
        # haber ailesi kendini yazdırır; diğer dört aile de (varsa) aynı
        # yerden bağlanır. Uygulama hazır olmadan model içe aktarılamaz,
        # bu yüzden ready() içinde.
        from . import kaynaklar  # noqa: F401
