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


def _ai_chat(user_msg, prev_msg, history, api_key):
    """Groq AI ile doğal dil anlama. Ücretsiz: console.groq.com'dan API key al."""
    from groq import Groq
    items = _build_flat_menu(None)
    menu_text = '\n'.join([f"- {i.get('name')} ({i.get('category')}) - {i.get('price')}" for i in items[:60]])
    system = f"""Sen samimi bir kafe garsonusun. Kullanıcıya menüden öneri sunuyorsun.
MENÜ:
{menu_text}

Kurallar:
- Her zaman samimi, sıcak ve yardımcı ol. Kısa cevap ver.
- "istemiyorum", "farklı", "başka" derse anlayıp ne istediğini sor.
- Menüde tam eşleşme yoksa bile benzer ürünler öner (örn: "kahve" yazdıysa Türk Kahvesi, Latte, Mocha öner).
- Öneri varsa: Önce 1 cümle cevap, sonra "ÖNERİLER:" satırı, sonra JSON array ["Ürün Adı", "Ürün Adı2"] (sadece menüdeki isimler).
- Öneri yoksa: Sadece samimi cevap yaz, alternatif sor. ÖNERİLER satırı ekleme.
- Asla "bulamadım" gibi soğuk ifadeler kullanma. Her zaman yardımcı ol.
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
    GROQ_API_KEY varsa: Her zaman Groq AI kullanılır.
    """
    try:
        body = json.loads(request.body or '{}')
        msg = (body.get('message') or '').strip()
        prev = (body.get('previous_message') or '').strip()
    except json.JSONDecodeError:
        msg = ''
        prev = ''

    groq_key = os.getenv('GROQ_API_KEY')
    msg_lower = msg.lower().strip()

    # Selamlaşma/teşekkür: Groq'a hiç sorma, hemen cevapla (API tasarrufu + tutarlı UX)
    greetings = ['selam', 'selamlar', 'merhaba', 'hey', 'hi', 'günaydın', 'iyi akşamlar', 'naber', 'nasılsın', 'slm', 'selamun aleyküm']
    if msg_lower in greetings or (len(msg.split()) <= 3 and any(g in msg_lower for g in greetings)):
        return _api_response({
            'success': True, 'greeting': True,
            'message': 'Merhaba! Hoş geldiniz 😊 Ne yemek veya içmek istersiniz?',
            'suggestions': [],
        })
    thanks_words = ['teşekkür', 'sağol', 'sağolun', 'eyvallah']
    if len(msg.split()) <= 3 and any(t in msg_lower for t in thanks_words):
        return _api_response({
            'success': True, 'greeting': True,
            'message': 'Rica ederim! Afiyet olsun. Başka bir şey isterseniz yazmanız yeterli 😊',
            'suggestions': [],
        })

    # GROQ varsa: AI dene. Hata olursa rule-based'e düş (asla "sorun oluştu" gösterme)
    if groq_key:
        try:
            result = _ai_chat(msg, prev, body.get('history', []), groq_key)
            if result:
                return _api_response(result)
        except Exception as e:
            import traceback
            logger.exception("Groq AI hatası (rule-based devreye giriyor): %s\n%s", str(e), traceback.format_exc())
            # Groq çalışmazsa aşağıdaki rule-based mantık devam edecek

    # GROQ yok veya hata verdi: Rule-based fallback (her zaman çalışır)
    context_hint = ''
    if prev:
        prev_lower = prev.lower()
        for trigger, data in AMBIGUOUS.items():
            if trigger in prev_lower:
                msg_lower = msg.lower()
                for opt_text, hint in data['options']:
                    hint_words = hint.split()[:4]
                    if any(w in msg_lower for w in hint_words):
                        context_hint = hint
                        break

    ambiguity = _check_ambiguity(msg)
    if ambiguity and not prev and len(msg.split()) <= 6:
        return _api_response({
            'success': True,
            'clarification': ambiguity['question'],
            'options': [o[0] for o in ambiguity['options']],
            'option_hints': [o[1] for o in ambiguity['options']],
            'suggestions': [],
        })

    msg_lower = msg.lower().strip()
    greetings = ['selam', 'selamlar', 'merhaba', 'hey', 'hi', 'günaydın', 'iyi akşamlar', 'naber', 'nasılsın']
    if msg_lower in greetings or (len(msg.split()) <= 2 and any(g in msg_lower for g in greetings)):
        return _api_response({
            'success': True,
            'greeting': True,
            'message': 'Merhaba! Hoş geldiniz 😊 Ne yemek veya içmek istersiniz?',
            'suggestions': [],
        })

    thanks_words = ['teşekkür', 'sağol', 'sağolun', 'eyvallah']
    if len(msg.split()) <= 3 and any(t in msg_lower for t in thanks_words):
        return _api_response({
            'success': True,
            'greeting': True,
            'message': 'Rica ederim! Afiyet olsun. Başka bir şey isterseniz yazmanız yeterli 😊',
            'suggestions': [],
        })

    rejection_words = ['istemiyorum', 'istemem', 'farklı', 'başka', 'olmadı', 'hayır', 'yok']
    if any(r in msg_lower for r in rejection_words):
        return _api_response({
            'success': True,
            'greeting': True,
            'message': 'Anladım! Ne tarz bir şey istersiniz? Örneğin: sıcak kahve, soğuk içecek, tatlı...',
            'suggestions': [],
        })

    suggestions, _ = _get_chat_suggestions(msg, context_hint)
    return _api_response({'success': True, 'suggestions': suggestions})
