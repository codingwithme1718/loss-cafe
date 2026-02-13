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
# Alkollü arama kelimeleri (alkollu/alkolu yazım varyantları)
ALCOHOL_KEYWORDS = {'bira', 'biralar', 'alkol', 'alkollü', 'alkolu', 'alkollu', 'şarap', 'şaraplar', 'kokteyl', 'kokteyller', 'viski', 'rakı', 'votka', 'cin'}
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


# Türkçe karakter normalizasyonu (icecek=içecek, bira eşleşmesi için)
_TR_NORM = str.maketrans('ıİğüşöçĞÜŞİÖÇ', 'iigusocGUSIOC')
def _normalize_for_match(text):
    if not text:
        return ''
    t = (text or '').lower().translate(_TR_NORM)
    return t.replace('\u0307', '')  # İ.lower() -> i+combining dot, temizle

def _extract_keywords(text):
    text = (text or '').lower()
    text = re.sub(r'[^\wğüşıöçĞÜŞİÖÇ\s]', ' ', text)
    return [w for w in text.split() if len(w) > 1 and w not in STOPWORDS]


def _get_chat_suggestions(message, context_hint=''):
    """context_hint: netleştirme cevabından gelen ek anahtar kelimeler."""
    full_msg = (message + ' ' + context_hint).strip().lower()
    full_norm = _normalize_for_match(full_msg)
    items = _build_flat_menu(None)
    words = _extract_keywords(full_msg)
    if not words:
        return items[:8], None

    def _cat_norm(c):
        return _normalize_for_match(c or '')

    # "alkollü içecek" / "bira" / "şarap" = Alkollü İçecekler
    want_alcohol = any(_cat_norm(w) in full_norm for w in ALCOHOL_KEYWORDS) or (
        ('alkol' in full_norm or 'alkoll' in full_norm) and ('icecek' in full_norm or 'içecek' in full_msg)
    )
    if want_alcohol:
        alcohol_items = [i for i in items if _cat_norm(i.get('category')) == _cat_norm(ALCOHOL_CATEGORY)]
        if not alcohol_items:
            alcohol_items = [i for i in items if any(
                kw in _cat_norm(i.get('name', '')) + _cat_norm(i.get('subcategory', ''))
                for kw in ['bira', 'sarap', 'kokteyl', 'raki', 'votka', 'viski', 'cin']
            )]
        if alcohol_items:
            return alcohol_items[:8], None

    want_drink = 'icecek' in full_norm or 'içecek' in full_msg or 'icecekler' in full_norm

    # "tatlı içecek" = tatlı İÇECEK (pasta değil) - önce kontrol
    want_sweet_drink = ('tatli' in full_norm or 'tatlı' in full_msg) and want_drink
    if want_sweet_drink:
        drink_items = [i for i in items if _cat_norm(i.get('category')) in {_cat_norm(c) for c in DRINK_CATEGORIES}]
        sweet_drinks = [i for i in drink_items if any(s in _cat_norm(i.get('name', '')) for s in SWEET_DRINK_NAMES)]
        other_drinks = [i for i in drink_items if i not in sweet_drinks]
        result = (sweet_drinks + other_drinks)[:8]
        if result:
            return result, None

    # "içecek istiyorum" / "icecek" = tüm içecek kategorileri
    if want_drink:
        drink_cats = DRINK_CATEGORIES | {ALCOHOL_CATEGORY}
        drink_items = [i for i in items if _cat_norm(i.get('category')) in {_cat_norm(c) for c in drink_cats}]
        if drink_items:
            return drink_items[:8], None

    scored = []
    for item in items:
        kw = (item.get('keywords') or '') + ' ' + (item.get('category') or '') + ' ' + (item.get('subcategory') or '') + ' ' + (item.get('name') or '')
        kw_norm = _normalize_for_match(kw)
        score = sum(4 for w in words if _normalize_for_match(w) in kw_norm)
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


def _ai_chat(user_msg, prev_msg, history, api_key):
    """Groq AI ile doğal dil anlama. DB: Category > SubCategory > SubSubCategory > SubSubSubCategory."""
    from groq import Groq
    items = _build_flat_menu(None)
    # Tam hiyerarşi: Kategori > Alt > Alt Alt > Ürün - Fiyat
    menu_lines = []
    for i in items[:80]:
        path = [i.get('category'), i.get('subcategory'), i.get('subsubcategory')]
        path = [p for p in path if p]
        path_str = ' > '.join(path) if path else i.get('category', '')
        menu_lines.append(f"- {path_str}: {i.get('name')} - {i.get('price')}")
    menu_text = '\n'.join(menu_lines)
    system = f"""Sen Loss Cafe'nin profesyonel menü asistanısın. Sadece aşağıdaki menüden öneri yapıyorsun.

MENÜ (Kategori > Alt Kategori > Ürün - Fiyat):
{menu_text}

KURALLAR (kesin uygula):
1. Her zaman menüden 2-6 ürün öner. Asla "bulamadım", "tam uyan ürün yok" deme.
2. Benzer eşleşme yeterli: "kahve" → Türk Kahvesi, Latte, Mocha; "tatlı" → pasta, cheesecake, brownie.
3. Öneri varsa: Kısa samimi cümle + "ÖNERİLER:" + JSON array ["Ürün Adı1", "Ürün Adı2"] (sadece menüdeki tam isimler).
4. "başka", "farklı" derse: Farklı kategoriden öner (örn. içecekten yemeğe geç).
5. Cevabın sıcak ve profesyonel olsun. Kısa tut.
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
            for n in names[:8]:
                name = (n if isinstance(n, str) else str(n)).strip()
                for i in items:
                    iname = (i.get("name") or "").lower()
                    nlow = name.lower()
                    if nlow in iname or iname in nlow:
                        if i not in suggestions:
                            suggestions.append(i)
                        break
        except Exception:
            pass
    if suggestions:
        return {"success": True, "message": text, "suggestions": suggestions}
    return {"success": True, "greeting": True, "message": text, "suggestions": []}


@csrf_exempt
@require_POST
def api_chat_suggest(request):
    """
    POST /api/chat/suggest
    Önce rule-based (menüden arama), Groq sadece fallback.
    """
    try:
        body = json.loads(request.body or '{}')
        msg = (body.get('message') or '').strip()
        prev = (body.get('previous_message') or '').strip()
    except json.JSONDecodeError:
        body = {}
        msg = ''
        prev = ''

    msg_lower = msg.lower().strip()
    items = _build_flat_menu(None)

    # 1. Selamlaşma -> menüden 8 öneri
    greetings = ['selam', 'selamlar', 'merhaba', 'hey', 'hi', 'günaydın', 'iyi akşamlar', 'naber', 'nasılsın', 'slm', 'selamun aleyküm']
    if not msg or msg_lower in greetings or (len(msg.split()) <= 3 and any(g in msg_lower for g in greetings)):
        return _api_response({
            'success': True, 'greeting': True,
            'message': 'Merhaba! Hoş geldiniz 😊 Ne yemek veya içmek istersiniz?',
            'suggestions': items[:8],
        })

    # 2. Teşekkür
    thanks_words = ['teşekkür', 'sağol', 'sağolun', 'eyvallah']
    if len(msg.split()) <= 4 and any(t in msg_lower for t in thanks_words):
        return _api_response({
            'success': True, 'greeting': True,
            'message': 'Rica ederim! Afiyet olsun. Başka bir şey isterseniz yazmanız yeterli 😊',
            'suggestions': items[:6],
        })

    # 3. Groq ÖNCELİKLİ (API key varsa)
    api_key = (os.environ.get('GROQ_API_KEY') or '').strip()
    if api_key:
        try:
            history = body.get('history', [])
            ai_result = _ai_chat(msg, prev, history, api_key)
            msg_text = ai_result.get('message', 'İşte size birkaç öneri 😊')
            sug = ai_result.get('suggestions', [])
            if not sug:
                sug, _ = _get_chat_suggestions(msg, '')
            if not sug:
                sug = items[:8]
            return _api_response({
                'success': True,
                'message': msg_text,
                'suggestions': sug[:8],
            })
        except Exception as e:
            logger.warning("Groq chat hatası, rule-based fallback: %s", str(e))

    # 4. Groq yok/hatalı: rule-based (içecek, bira, kahve vb.)
    suggestions, _ = _get_chat_suggestions(msg, '')
    if suggestions:
        if any(_normalize_for_match(w) in _normalize_for_match(msg_lower) for w in ALCOHOL_KEYWORDS):
            return _api_response({
                'success': True,
                'message': 'İşte alkollü içeceklerimizden birkaç öneri 😊',
                'suggestions': suggestions[:8],
            })
        return _api_response({
            'success': True,
            'message': 'İşte size birkaç öneri 😊',
            'suggestions': suggestions[:8],
        })

    return _api_response({
        'success': True,
        'message': 'İşte size birkaç lezzetli seçenek 😊',
        'suggestions': items[:8],
    })
