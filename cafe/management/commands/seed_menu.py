"""
Örnek menü verisi ekler. Çalıştırmak için:
  python manage.py seed_menu
  python manage.py seed_menu --force   # Kategorileri de ekler (mevcut olsa bile)
"""
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from cafe.models import MenuBackground, Category, SubCategory, SubSubCategory, SubSubSubCategory

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _make_placeholder(w=200, h=200, color=(13, 92, 46)):
    """Basit placeholder JPEG oluşturur."""
    if not HAS_PIL:
        return None
    img = Image.new('RGB', (w, h), color)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Örnek kategori ve menü verisi ekler"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Kategorileri zorla ekle')

    def handle(self, *args, **options):
        bg, created = MenuBackground.objects.get_or_create(
            defaults={
                'title': 'Loss Cafe',
                'color': '#0d5c2e',
                'description': 'Sıcak ortam, lezzetli menü. Kahve, nargile ve tatlılar.',
                'href_instagram': 'https://instagram.com',
                'href_facebook': 'https://facebook.com',
                'href_twitter': '',
                'name': 'Loss Cafe',
                'address': 'Örnek Mah. Cafe Sok. No:1',
                'telephone': '+90 212 000 00 00',
                'email': 'info@losscafe.com.tr',
            },
            title='Loss Cafe'
        )
        if created:
            self.stdout.write("MenuBackground oluşturuldu.")

        # Placeholder görseller ekle (yoksa)
        if HAS_PIL:
            try:
                if not (bg.icon_image and bg.icon_image.name):
                    data = _make_placeholder(80, 80, (201, 162, 39))
                    if data:
                        bg.icon_image.save('logo.jpg', data, save=True)
                        self.stdout.write("Logo placeholder eklendi.")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Logo eklenemedi: {e}"))
            try:
                if not (bg.image and bg.image.name):
                    data = _make_placeholder(800, 600, (13, 92, 46))
                    if data:
                        bg.image.save('bg.jpeg', data, save=True)
                        self.stdout.write("Arka plan placeholder eklendi.")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Arka plan eklenemedi: {e}"))

        if Category.objects.count() >= 10 and not options.get('force'):
            self.stdout.write("Yeterli kategori mevcut, seed atlanıyor.")
            return

        data = [
            ("Sıcak İçecekler", [
                ("Kahveler", [
                    ("Türk Kahvesi", "45 TL"),
                    ("Filtre Kahve", "55 TL"),
                    ("Latte", "65 TL"),
                    ("Cappuccino", "65 TL"),
                    ("Americano", "55 TL"),
                    ("Espresso", "45 TL"),
                    ("Mocha", "70 TL"),
                ]),
                ("Çaylar", [
                    ("Demlik Çay", "25 TL"),
                    ("Earl Grey", "35 TL"),
                    ("Yeşil Çay", "35 TL"),
                    ("Adaçayı", "30 TL"),
                    ("Ihlamur", "30 TL"),
                ]),
                ("Sıcak Çikolata", [
                    ("Sıcak Çikolata", "55 TL"),
                    ("Sütlü Sıcak Çikolata", "60 TL"),
                ]),
            ]),
            ("Soğuk İçecekler", [
                ("Limonatalar", [
                    ("Limonata", "45 TL"),
                    ("Nane Limonata", "50 TL"),
                    ("Çilek Limonata", "55 TL"),
                ]),
                ("Smoothie", [
                    ("Mango Smoothie", "65 TL"),
                    ("Çilek Smoothie", "60 TL"),
                    ("Karışık Meyve Smoothie", "70 TL"),
                ]),
                ("Buzlu Kahve", [
                    ("Buzlu Americano", "60 TL"),
                    ("Buzlu Latte", "70 TL"),
                    ("Cold Brew", "65 TL"),
                ]),
            ]),
            ("Tatlılar", [
                ("Pastalar", [
                    ("Cheesecake", "85 TL"),
                    ("Brownie", "75 TL"),
                    ("Tiramisu", "90 TL"),
                ]),
                ("Kekler", [
                    ("Havuçlu Kek", "65 TL"),
                    ("Meyveli Kek", "70 TL"),
                ]),
            ]),
            ("Nargile", [
                ("Klasik Nargile", [
                    ("Elma Nargile", "120 TL"),
                    ("Çilek Nargile", "120 TL"),
                    ("Muz Nargile", "120 TL"),
                    ("Karışık Meyve Nargile", "130 TL"),
                ]),
                ("Özel Nargile", [
                    ("Double Apple", "140 TL"),
                    ("Blue Mist", "140 TL"),
                ]),
            ]),
            ("Atıştırmalıklar", [
                ("Tostlar", [
                    ("Kaşarlı Tost", "55 TL"),
                    ("Karışık Tost", "65 TL"),
                ]),
                ("Sandviçler", [
                    ("Tavuklu Sandviç", "75 TL"),
                    ("Peynirli Sandviç", "65 TL"),
                ]),
            ]),
            ("Meyve Suları", [
                ("Taze Sıkılmış", [
                    ("Portakal Suyu", "50 TL"),
                    ("Elma Suyu", "45 TL"),
                    ("Havuç Suyu", "55 TL"),
                ]),
            ]),
            ("Salatalar", [
                ("Yeşil Salatalar", [
                    ("Çoban Salata", "65 TL"),
                    ("Sezar Salata", "85 TL"),
                    ("Mevsim Salata", "60 TL"),
                ]),
            ]),
            ("Ana Yemekler", [
                ("Izgara", [
                    ("Tavuk Şiş", "120 TL"),
                    ("Köfte", "110 TL"),
                    ("Kuzu Pirzola", "150 TL"),
                ]),
            ]),
            ("Çorbalar", [
                ("Sıcak Çorbalar", [
                    ("Mercimek Çorbası", "45 TL"),
                    ("Ezogelin", "45 TL"),
                    ("Tavuk Suyu", "50 TL"),
                ]),
            ]),
            ("Meyveli İçecekler", [
                ("Meyve Kokteylleri", [
                    ("Mango Mojito (Alkolsüz)", "65 TL"),
                    ("Çilekli Smoothie", "60 TL"),
                ]),
            ]),
            ("Alkollü İçecekler", [
                ("Biralar", [
                    ("Efes Pilsen", "55 TL"),
                    ("Efes Dark", "60 TL"),
                    ("Tuborg", "55 TL"),
                    ("Corona", "75 TL"),
                    ("Heineken", "65 TL"),
                ]),
                ("Şaraplar", [
                    ("Kırmızı Şarap (Kadehi)", "85 TL"),
                    ("Beyaz Şarap (Kadehi)", "85 TL"),
                    ("Gül Şarabı (Kadehi)", "90 TL"),
                    ("Şişe Kırmızı Şarap", "350 TL"),
                    ("Şişe Beyaz Şarap", "350 TL"),
                ]),
                ("Kokteyller", [
                    ("Mojito", "120 TL"),
                    ("Margarita", "130 TL"),
                    ("Piña Colada", "125 TL"),
                    ("Sex on the Beach", "130 TL"),
                    ("Long Island", "140 TL"),
                    ("Cosmopolitan", "135 TL"),
                ]),
                ("Rakı & Votka", [
                    ("Rakı (Tek)", "95 TL"),
                    ("Rakı (Duble)", "180 TL"),
                    ("Votka (Tek)", "85 TL"),
                    ("Votka (Duble)", "165 TL"),
                ]),
                ("Viski & Cin", [
                    ("Viski (Tek)", "95 TL"),
                    ("Viski (Duble)", "185 TL"),
                    ("Jack Daniel's", "110 TL"),
                    ("Cin Tonic", "100 TL"),
                ]),
            ]),
        ]

        for order, (cat_name, subcats) in enumerate(data):
            cat, _ = Category.objects.get_or_create(name=cat_name, defaults={"order": order})
            for so, (sub_name, items) in enumerate(subcats):
                sub, _ = SubCategory.objects.get_or_create(
                    name=sub_name, category=cat,
                    defaults={"order": so}
                )
                subsub, _ = SubSubCategory.objects.get_or_create(
                    name="Çeşitler", subcategory=sub,
                    defaults={"order": 0}
                )
                for io, (item_name, price) in enumerate(items):
                    SubSubSubCategory.objects.get_or_create(
                        name=item_name,
                        subsubcategory=subsub,
                        defaults={"price": price, "order": io}
                    )

        # Kategorilere placeholder görsel ekle
        if HAS_PIL:
            colors = [(13, 92, 46), (8, 68, 34), (201, 162, 39), (150, 120, 30), (92, 60, 20)]
            for i, cat in enumerate(Category.objects.all()):
                if not (cat.image and cat.image.name):
                    try:
                        c = colors[i % len(colors)]
                        data = _make_placeholder(300, 225, c)
                        if data:
                            cat.image.save(f'cat_{cat.id}.jpg', data, save=True)
                    except Exception:
                        pass

        self.stdout.write(self.style.SUCCESS(f"Seed tamamlandı. {Category.objects.count()} kategori eklendi."))
