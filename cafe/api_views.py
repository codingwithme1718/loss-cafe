"""
Public API for external access to menu data.
Returns all categories, subcategories, and prices in JSON format.
AI Chat: Groq (ücretsiz) - GROQ_API_KEY ile aktif olur.
"""
import json
import logging
import os
import re
from django.http import JsonResponse

logger = logging.getLogger(__name__)
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from .models import Category, SubCategory, SubSubCategory, SubSubSubCategory


def _url(request, url):
    """Build absolute URL for API consumers."""
    if not url:
        return None
    return request.build_absolute_uri(url) if request else url


def _build_menu_tree(request=None):
    """Build full menu hierarchy with prices for API response."""
    categories = Category.objects.all().prefetch_related(
        'subcategories__subsubcategories__subsubsubcategories'
    )
    data = []
    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description or '',
            'image_url': _url(request, cat.image.url if cat.image else None),
            'order': cat.order,
            'subcategories': []
        }
        for sub in cat.subcategories.all():
            sub_data = {
                'id': sub.id,
                'name': sub.name,
                'description': sub.description or '',
                'price': sub.price,
                'image_url': _url(request, sub.image.url if sub.image else None),
                'order': sub.order,
                'subsubcategories': []
            }
            for subsub in sub.subsubcategories.all():
                subsub_data = {
                    'id': subsub.id,
                    'name': subsub.name,
                    'description': subsub.description or '',
                    'price': subsub.price,
                    'image_url': _url(request, subsub.image.url if subsub.image else None),
                    'order': subsub.order,
                    'subsubsubcategories': []
                }
                for subsubsub in subsub.subsubsubcategories.all():
                    subsub_data['subsubsubcategories'].append({
                        'id': subsubsub.id,
                        'name': subsubsub.name,
                        'description': subsubsub.description or '',
                        'price': subsubsub.price,
                        'image_url': _url(request, subsubsub.image.url if subsubsub.image else None),
                        'order': subsubsub.order,
                    })
                sub_data['subsubcategories'].append(subsub_data)
            cat_data['subcategories'].append(sub_data)
        data.append(cat_data)
    return data


def _build_flat_menu(request=None):
    """Build flat list of all items with prices for easy consumption."""
    items = []
    for cat in Category.objects.all().order_by('order'):
        for sub in cat.subcategories.all().order_by('order'):
            if sub.price:
                parts = [cat.name, sub.name, sub.description or '']
                items.append({
                    'id': sub.id,
                    'category': cat.name,
                    'name': sub.name,
                    'description': sub.description or '',
                    'price': sub.price,
                    'image_url': _url(request, sub.image.url if sub.image else None),
                    'level': 'subcategory',
                    'keywords': ' '.join(p for p in parts if p).lower(),
                })
            for subsub in sub.subsubcategories.all().order_by('order'):
                if subsub.price:
                    parts = [cat.name, sub.name, subsub.name, subsub.description or '']
                    items.append({
                        'id': subsub.id,
                        'category': cat.name,
                        'subcategory': sub.name,
                        'name': subsub.name,
                        'description': subsub.description or '',
                        'price': subsub.price,
                        'image_url': _url(request, subsub.image.url if subsub.image else None),
                        'level': 'subsubcategory',
                        'keywords': ' '.join(p for p in parts if p).lower(),
                    })
                for subsubsub in subsub.subsubsubcategories.all().order_by('order'):
                    parts = [cat.name, sub.name, subsub.name, subsubsub.name, subsubsub.description or '']
                    items.append({
                        'id': subsubsub.id,
                        'category': cat.name,
                        'subcategory': sub.name,
                        'subsubcategory': subsub.name,
                        'name': subsubsub.name,
                        'description': subsubsub.description or '',
                        'price': subsubsub.price,
                        'image_url': _url(request, subsubsub.image.url if subsubsub.image else None),
                        'level': 'subsubsubcategory',
                        'keywords': ' '.join(p for p in parts if p).lower(),
                    })
    return items


def _api_response(data):
    """JSON response with CORS headers for external access."""
    r = JsonResponse(data)
    r['Access-Control-Allow-Origin'] = '*'
    return r


@require_GET
@cache_page(60 * 5)  # Cache for 5 minutes
def api_menu_full(request):
    """
    GET /api/menu/
    Returns full menu tree: categories -> subcategories -> subsubcategories -> subsubsubcategories
    Dış projelerden erişim: GET https://losscafe.com.tr/api/menu/
    """
    data = _build_menu_tree(request)
    return _api_response({'success': True, 'menu': data})


@require_GET
@cache_page(60 * 5)
def api_menu_flat(request):
    """
    GET /api/menu/flat/
    Returns flat list of all items with prices (for price lists, integrations).
    Dış projelerden erişim: GET https://losscafe.com.tr/api/menu/flat/
    """
    data = _build_flat_menu(request)
    return _api_response({'success': True, 'items': data})


STOPWORDS = {'ve', 'ile', 'bir', 'ne', 'var', 'mi', 'mu', 'mı', 'musun', 'mısın', 'önerin', 'öneri', 'önerir',
             'bilmiyorum', 'istiyorum', 'istersiniz', 'istiyor', 'yemek', 'içmek', 'falan', 'filan', 'şey',
             'şeyler', 'ama', 'fakat', 'ancak', 'lütfen', 'teşekkür', 'sağol', 'nedir', 'nasıl', 'hangi'}

# İçecek kategorileri (tatlı içecek = bu kategorilerden tatlı olanlar)
DRINK_CATEGORIES = {'sıcak içecekler', 'soğuk içecekler', 'meyve suları', 'meyveli içecekler'}
# Alkollü içecek kategorisi (bira, şarap vb.)
ALCOHOL_CATEGORY = 'alkollü içecekler'
# Alkollü arama kelimeleri
ALCOHOL_KEYWORDS = {'bira', 'biralar', 'alkol', 'alkollü', 'şarap', 'şaraplar', 'kokteyl', 'kokteyller', 'viski', 'rakı', 'votka', 'cin'}
# Tatlı içecekler (isimde geçen - öncelik sırası)
SWEET_DRINK_NAMES = ['mocha', 'çikolata', 'limonata', 'smoothie', 'buzlu latte', 'mango', 'çilek', 'portakal', 'elma', 'havuç', 'latte', 'cappuccino', 'mojito']

# Belirsiz durumlar: netleştirme sorusu sor (sıcak, samimi dil)
AMBIGUOUS = {
    'tatlı': {
        'question': 'Anladım! Tatlı derken hangisini kastediyorsunuz? Size tam istediğinizi önerebilmek için soruyorum 😊',
        'options': [
            ('Pasta, kek, cheesecake gibi tatlılar', 'tatlılar pasta kek cheesecake brownie tiramisu'),
            ('Lezzetli ana yemek (ızgara, köfte vb.)', 'ana yemek ızgara köfte tavuk'),
        ],
    },
    'içecek': {
        'question': 'Tabii! Hangi tür içecek istersiniz? Sıcak mı soğuk mu tercih edersiniz?',
        'options': [
            ('Sıcak (kahve, çay)', 'sıcak kahve çay'),
            ('Soğuk (limonata, smoothie, buzlu kahve)', 'soğuk limonata smoothie buzlu'),
        ],
    },
}


def _extract_keywords(text):
    text = (text or '').lower() 
    text = re.sub(r'[^\wğüşıöçĞÜŞİÖÇ\s]', ' ', text)
    return [w for w in text.split() if len(w) > 1 and w not in STOPWORDS]


def _get_chat_suggestions(message, context_hint=''):
    """context_hint: netleştirme cevabından gelen ek anahtar kelimeler."""
    full_msg = (message + ' ' + context_hint).strip().lower()
    items = _build_flat_menu(None)
    words = _extract_keywords(full_msg)
    if not words:
        return items[:8], None

    # "bira öner" / "alkollü içecek" / "şarap" = Alkollü İçecekler kategorisinden
    want_alcohol = any(w in full_msg for w in ALCOHOL_KEYWORDS)
    if want_alcohol:
        alcohol_items = [i for i in items if (i.get('category') or '').lower() == ALCOHOL_CATEGORY]
        if alcohol_items:
            return alcohol_items[:8], None

    # "tatlı içecek" / "tatlı bir içecek" = tatlı İÇECEK isteniyor, pasta/kek DEĞİL
    want_sweet_drink = ('tatlı' in full_msg or 'tatli' in full_msg) and (
        'içecek' in full_msg or 'icecek' in full_msg or 'içecekler' in full_msg
    )
    if want_sweet_drink:
        drink_items = [
            i for i in items
            if (i.get('category') or '').lower() in DRINK_CATEGORIES
        ]
        # Tatlı olanları öne al: mocha, çikolata, limonata, smoothie vb.
        sweet_drinks = []
        other_drinks = []
        for i in drink_items:
            name = (i.get('name') or '').lower()
            if any(s in name for s in SWEET_DRINK_NAMES):
                sweet_drinks.append(i)
            else:
                other_drinks.append(i)
        result = (sweet_drinks + other_drinks)[:8]
        if result:
            return result, None

    scored = []
    for item in items:
        kw = (item.get('keywords') or '') + ' ' + (item.get('category') or '') + ' ' + (item.get('name') or '')
        kw = kw.lower()
        score = sum(4 for w in words if w in kw)
        if score > 0:
            scored.append((item, score))
    scored.sort(key=lambda x: -x[1])
    seen = set()
    result = []
    for item, _ in scored:
        k = item.get('name', '') + (item.get('category') or '')
        if k not in seen:
            seen.add(k)
            result.append(item)
            if len(result) >= 8:
                break
    return result, None


def _check_ambiguity(message):
    """Belirsiz sorgu varsa netleştirme sorusu döndür."""
    msg = (message or '').lower()
    # "tatlı içecek" / "tatlı bir içecek" = net, tatlı içecek isteniyor
    if 'tatlı' in msg and ('içecek' in msg or 'icecek' in msg):
        return None
    for trigger, data in AMBIGUOUS.items():
        if trigger not in msg:
            continue
        # Zaten net mi? (pasta, kek, ana yemek, kahve vb. yazdıysa atla)
        clear_words = ['pasta', 'kek', 'cheesecake', 'brownie', 'tiramisu', 'ana yemek', 'ızgara', 'köfte', 'kahve', 'çay', 'limonata', 'smoothie', 'buzlu']
        if any(w in msg for w in clear_words):
            continue
        return data
    return None


def _menu_line_for_ai(item):
    """Tam hiyerarşi: Kategori > Alt Kategori > Alt Alt Kategori > Ürün - Fiyat"""
    parts = [i for i in [item.get('category'), item.get('subcategory'), item.get('subsubcategory'), item.get('name')] if i]
    return ' > '.join(parts) + f" - {item.get('price', '')}"


def _ai_chat(user_msg, prev_msg, history, api_key):
    """Groq AI ile doğal dil anlama. Ücretsiz: console.groq.com'dan API key al."""
    from groq import Groq
    items = _build_flat_menu(None)
    menu_text = '\n'.join([f"- {_menu_line_for_ai(i)}" for i in items[:120]])
    system = f"""Sen samimi bir kafe garsonusun. Kullanıcıya menüden öneri sunuyorsun.
MENÜ:
{menu_text}

ZORUNLU KURALLAR:
- ASLA "bulamadım", "tam uyan ürün bulamadım", "eşleşen ürün yok" gibi ifadeler kullanma. YASAK.
- Her mesajda MUTLAKA ÖNERİLER ver. Kullanıcı ne yazarsa yazsın, menüden en az 2-4 ürün öner.
- Belirsiz veya anlaşılmayan istekte: Popüler karışık öner (kahve, tatlı, soğuk içecek, bira vb. menüden).
- "bira/şarap/alkollü" = Alkollü İçecekler > Biralar/Şaraplar/Kokteyller. "kahve" = Sıcak İçecekler > Kahveler. "tatlı" = Tatlılar.
- Kategori, alt kategori veya ürün adında benzer kelime varsa mutlaka öner.
- Format: 1 samimi cümle + "ÖNERİLER:" + JSON array ["Ürün1", "Ürün2", ...] (sadece menüdeki tam isimler).
- "istemiyorum/farklı/başka" derse: "Ne istersiniz?" de ve yine 2-4 ürün öner.
"""
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:  # Son 6 mesaj
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")[:200]})
    if prev_msg:
        messages.append({"role": "user", "content": prev_msg[:150]})
        messages.append({"role": "assistant", "content": "[Önceki öneri verildi]"})
    messages.append({"role": "user", "content": user_msg})
    client = Groq(api_key=api_key)
    models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    resp = None
    last_err = None
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.2,
            )
            break
        except Exception as e:
            last_err = e
            logger.info("Groq model %s başarısız, sonraki deneniyor: %s", model, str(e))
            continue
    if resp is None:
        raise last_err or Exception("Groq API yanıt vermedi")
    text = (resp.choices[0].message.content or "").strip()
    suggestions = []
    if "ÖNERİLER:" in text:
        parts = text.split("ÖNERİLER:")
        text = parts[0].strip()
        try:
            json_str = parts[1].strip().strip("[]")
            names = json.loads("[" + json_str + "]") if json_str else []
            for n in names[:12]:
                name = (n if isinstance(n, str) else str(n)).strip().lower()
                for i in items:
                    if len(suggestions) >= 8:
                        break
                    search_in = ' '.join([
                        i.get('category') or '', i.get('subcategory') or '',
                        i.get('subsubcategory') or '', i.get('name') or ''
                    ]).lower()
                    if name in search_in or (i.get('name') or '').lower() in name:
                        if i not in suggestions:
                            suggestions.append(i)
        except Exception:
            pass
    # AI "bulamadım" dediyse veya öneri vermediyse: popüler karışık öner
    fail_phrases = ['bulamadım', 'bulunamadı', 'tam uyan ürün', 'eşleşen ürün yok', 'eşleşme yok']
    if not suggestions and any(p in text.lower() for p in fail_phrases):
        text = "Tabii! Size birkaç lezzetli seçenek önereyim 😊"
        suggestions = items[:8]
    if suggestions:
        return {"success": True, "message": text, "suggestions": suggestions}
    # Öneri yoksa yine de karışık ver
    if not suggestions:
        suggestions = items[:6]
        if not text.strip().endswith(('!', '.', '?')):
            text = (text + " İşte size birkaç öneri:").strip() if text else "İşte size birkaç lezzetli seçenek 😊"
    return {"success": True, "greeting": True, "message": text, "suggestions": suggestions}


@csrf_exempt
@require_POST
def api_chat_suggest(request):
    """
    POST /api/chat/suggest
    Sadece Groq AI kullanılır. Kategori, subcategory, subsubcategory her yerde arar.
    """
    try:
        body = json.loads(request.body or '{}')
        msg = (body.get('message') or '').strip()
        prev = (body.get('previous_message') or '').strip()
    except json.JSONDecodeError:
        msg = ''
        prev = ''

    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        return _api_response({
            'success': True, 'message': 'Şu an öneri veremiyorum. Lütfen menüden seçin.', 'suggestions': [],
        })

    # Selamlaşma: Groq'a sorma, direkt menüden öner (models.py'deki Category/SubCategory/SubSubCategory/SubSubSubCategory)
    greetings = ['selam', 'selamlar', 'merhaba', 'hey', 'hi', 'günaydın', 'iyi akşamlar', 'naber', 'nasılsın', 'slm', 'selamun aleyküm', 'hoşgeldin']
    msg_lower = msg.lower().strip()
    if not msg or msg_lower in greetings or (len(msg.split()) <= 3 and any(g in msg_lower for g in greetings)):
        items = _build_flat_menu(None)
        return _api_response({
            'success': True, 'greeting': True,
            'message': 'Merhaba! Hoş geldiniz 😊 Ne yemek veya içmek istersiniz?',
            'suggestions': items[:8],
        })

    try:
        result = _ai_chat(msg, prev, body.get('history', []), groq_key)
        return _api_response(result)
    except Exception as e:
        logger.exception("Groq AI hatası: %s", str(e))
        return _api_response({
            'success': True, 'message': 'Üzgünüm, şu an yanıt veremiyorum. Menüden seçebilirsiniz.', 'suggestions': [],
        })
