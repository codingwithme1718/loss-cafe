import json
import logging
import os
import re
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from .models import Category, SubCategory, SubSubCategory, SubSubSubCategory

logger = logging.getLogger(__name__)

# ---------------------
# Menü & Menü Flat Builder
# ---------------------
def _url(request, url):
    if not url:
        return None
    return request.build_absolute_uri(url) if request else url

def _build_menu_tree(request=None, lang='tr'):
    categories = Category.objects.all().prefetch_related(
        'subcategories__subsubcategories__subsubsubcategories'
    )
    data = []
    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': (cat.name_en or cat.name) if lang == 'en' else cat.name,
            'description': (cat.description_en or cat.description or '') if lang == 'en' else (cat.description or ''),
            'image_url': _url(request, cat.image.url if cat.image else None),
            'order': cat.order,
            'subcategories': []
        }
        for sub in cat.subcategories.all():
            sub_data = {
                'id': sub.id,
                'name': (sub.name_en or sub.name) if lang == 'en' else sub.name,
                'description': (sub.description_en or sub.description or '') if lang == 'en' else (sub.description or ''),
                'price': sub.price,
                'image_url': _url(request, sub.image.url if sub.image else None),
                'order': sub.order,
                'subsubcategories': []
            }
            for subsub in sub.subsubcategories.all():
                subsub_data = {
                    'id': subsub.id,
                    'name': (subsub.name_en or subsub.name) if lang == 'en' else subsub.name,
                    'description': (subsub.description_en or subsub.description or '') if lang == 'en' else (subsub.description or ''),
                    'price': subsub.price,
                    'image_url': _url(request, subsub.image.url if subsub.image else None),
                    'order': subsub.order,
                    'subsubsubcategories': []
                }
                for subsubsub in subsub.subsubsubcategories.all():
                    subsub_data['subsubsubcategories'].append({
                        'id': subsubsub.id,
                        'name': (subsubsub.name_en or subsubsub.name) if lang == 'en' else subsubsub.name,
                        'description': (subsubsub.description_en or subsubsub.description or '') if lang == 'en' else (subsubsub.description or ''),
                        'price': subsubsub.price,
                        'image_url': _url(request, subsubsub.image.url if subsubsub.image else None),
                        'order': subsubsub.order,
                    })
                sub_data['subsubcategories'].append(subsub_data)
            cat_data['subcategories'].append(sub_data)
        data.append(cat_data)
    return data

def _build_flat_menu(request=None, lang='tr'):
    items = []
    for cat in Category.objects.all().order_by('order'):
        for sub in cat.subcategories.all().order_by('order'):
            if sub.price:
                sub_name = (sub.name_en or sub.name) if lang == 'en' else sub.name
                sub_desc = (sub.description_en or sub.description or '') if lang == 'en' else (sub.description or '')
                cat_name = (cat.name_en or cat.name) if lang == 'en' else cat.name
                parts = [cat_name, sub_name, sub_desc]
                items.append({
                    'id': sub.id,
                    'category': cat_name,
                    'name': sub_name,
                    'description': sub_desc,
                    'price': sub.price,
                    'image_url': _url(request, sub.image.url if sub.image else None),
                    'level': 'subcategory',
                    'keywords': ' '.join(p for p in parts if p).lower(),
                })
            for subsub in sub.subsubcategories.all().order_by('order'):
                if subsub.price:
                    subsub_name = (subsub.name_en or subsub.name) if lang == 'en' else subsub.name
                    subsub_desc = (subsub.description_en or subsub.description or '') if lang == 'en' else (subsub.description or '')
                    cat_name = (cat.name_en or cat.name) if lang == 'en' else cat.name
                    sub_name = (sub.name_en or sub.name) if lang == 'en' else sub.name
                    parts = [cat_name, sub_name, subsub_name, subsub_desc]
                    items.append({
                        'id': subsub.id,
                        'category': cat_name,
                        'subcategory': sub_name,
                        'name': subsub_name,
                        'description': subsub_desc,
                        'price': subsub.price,
                        'image_url': _url(request, subsub.image.url if subsub.image else None),
                        'level': 'subsubcategory',
                        'keywords': ' '.join(p for p in parts if p).lower(),
                    })
                for subsubsub in subsub.subsubsubcategories.all().order_by('order'):
                    subsubsub_name = (subsubsub.name_en or subsubsub.name) if lang == 'en' else subsubsub.name
                    subsubsub_desc = (subsubsub.description_en or subsubsub.description or '') if lang == 'en' else (subsubsub.description or '')
                    cat_name = (cat.name_en or cat.name) if lang == 'en' else cat.name
                    sub_name = (sub.name_en or sub.name) if lang == 'en' else sub.name
                    subsub_name = (subsub.name_en or subsub.name) if lang == 'en' else subsub.name
                    parts = [cat_name, sub_name, subsub_name, subsubsub_name, subsubsub_desc]
                    items.append({
                        'id': subsubsub.id,
                        'category': cat_name,
                        'subcategory': sub_name,
                        'subsubcategory': subsub_name,
                        'name': subsubsub_name,
                        'description': subsubsub_desc,
                        'price': subsubsub.price,
                        'image_url': _url(request, subsubsub.image.url if subsubsub.image else None),
                        'level': 'subsubsubcategory',
                        'keywords': ' '.join(p for p in parts if p).lower(),
                    })
    return items

# ---------------------
# Keyword Normalization
# ---------------------
STOPWORDS = {'ve', 'ile', 'bir', 'ne', 'var', 'mi', 'mu', 'mı', 'musun', 'mısın', 'önerin', 'öneri', 'önerir',
             'bilmiyorum', 'istiyorum', 'istersiniz', 'istiyor', 'istiyorsun', 'istersen', 'yemek', 'içmek',
             'falan', 'filan', 'şey', 'şeyler', 'ama', 'fakat', 'ancak', 'lütfen', 'teşekkür', 'sağol', 'nedir', 'nasıl', 'hangi'}

DRINK_CATEGORIES = {'sıcak içecekler', 'soğuk içecekler', 'meyve suları', 'meyveli içecekler'}
ALCOHOL_CATEGORY = 'alkollü içecekler'
ALCOHOL_KEYWORDS = {'bira', 'biralar', 'alkol', 'alkollü', 'şarap', 'kokteyl', 'viski', 'rakı', 'votka', 'cin', 'tekila', 'tequila', 'mimoza'}
SWEET_DRINK_NAMES = ['mocha', 'çikolata', 'limonata', 'smoothie', 'buzlu latte', 'mango', 'çilek', 'portakal', 'elma', 'havuç', 'latte', 'cappuccino', 'mojito']

MENU_SUBCAT_MAP = [
    ('burger', 'burgerler'),
    ('pizza', 'pizzalar'),
    ('bira', 'biralar'),
    ('kahve', 'dunya kahveleri'),
    ('çay', 'caylar'),
    ('makarna', 'makarnalar'),
    ('salata', 'salatalar'),
    ('tatlı', 'tatlilar'),
    ('tavuk', 'tavuk yemekleri'),
    ('et ', 'et yemekleri'),
    ('köfte', 'et yemekleri'),
    ('kokteyl', 'alkollu icecekler'),
    ('viski', 'alkollu icecekler'),
    ('şarap', 'alkollu icecekler'),
]

_TR_NORM = str.maketrans('ıİğüşöçĞÜŞİÖÇ', 'iigusocGUSIOC')
def _normalize(text):
    if not text: return ''
    return text.lower().translate(_TR_NORM).replace('\u0307','')

def _extract_keywords(text):
    text = re.sub(r'[^\wğüşıöçĞÜŞİÖÇ\s]', ' ', text.lower())
    return [w for w in text.split() if len(w) > 1 and w not in STOPWORDS]

# ---------------------
# Ambiguity Checker
# ---------------------
AMBIGUOUS = {
    'tatlı': {
        'question': 'Anladım! Tatlı derken hangisini kastediyorsunuz? 😊',
        'options': [
            ('Pasta, kek, cheesecake vb.', 'tatlılar pasta kek cheesecake brownie tiramisu'),
            ('Lezzetli ana yemek (ızgara, köfte vb.)', 'ana yemek ızgara köfte tavuk'),
        ],
    },
    'içecek': {
        'question': 'Tabii! Hangi tür içecek istersiniz? Sıcak mı soğuk mu?',
        'options': [
            ('Sıcak (kahve, çay)', 'sıcak kahve çay'),
            ('Soğuk (limonata, smoothie, buzlu kahve)', 'soğuk limonata smoothie buzlu'),
        ],
    },
}

def _check_ambiguity(msg):
    msg = (msg or '').lower()
    for t, data in AMBIGUOUS.items():
        if t in msg:
            clear_words = ['pasta','kek','cheesecake','brownie','tiramisu','ana yemek','ızgara','köfte','kahve','çay','limonata','smoothie','buzlu']
            if any(w in msg for w in clear_words): continue
            return data
    return None

# ---------------------
# Chat Suggestion Fallback (multi-intent support)
# ---------------------
def _get_chat_suggestions(msg):
    msg_norm = _normalize(msg)
    items = _build_flat_menu(None)
    words = _extract_keywords(msg)
    if not words: return items[:8], None

    # Çoklu intent: alkol + içecek + tatlı
    alcohol_items = [i for i in items if _normalize(i.get('category'))==_normalize(ALCOHOL_CATEGORY)]
    drink_items = [i for i in items if _normalize(i.get('category')) in {_normalize(c) for c in DRINK_CATEGORIES}]
    sweet_drink_items = [i for i in drink_items if any(s in _normalize(i.get('name','')) for s in SWEET_DRINK_NAMES)]
    sweet_items = [i for i in items if 'tatlı' in _normalize(i.get('subcategory') or '')]

    suggestions = []
    if any(w in msg_norm for w in ALCOHOL_KEYWORDS):
        suggestions += alcohol_items
    if 'icecek' in msg_norm or 'içecek' in msg_norm:
        suggestions += sweet_drink_items + drink_items
    if 'tatlı' in msg_norm:
        suggestions += sweet_items

    # Keyword scoring fallback
    if not suggestions:
        scored = []
        seen = set()
        for i in items:
            kw = (i.get('keywords') or '') + ' ' + (i.get('category') or '') + ' ' + (i.get('subcategory') or '')
            score = sum(4 for w in words if _normalize(w) in _normalize(kw))
            if score > 0:
                k = i.get('name','') + (i.get('category') or '')
                if k not in seen:
                    scored.append((i, score))
                    seen.add(k)
        scored.sort(key=lambda x:-x[1])
        suggestions = [i for i,_ in scored]

    return suggestions[:8], None

# ---------------------
# Groq Chat Integration
# ---------------------
def _ai_chat(user_msg, prev_msg, history, api_key):
    from groq import Groq
    items = _build_flat_menu(None)
    menu_text = "\n".join([i['name'] + f" - {i['price']}" for i in items[:50]])
    msg_norm = _normalize(user_msg or '')

    cat_hint = ''
    for kw, subcat_norm in MENU_SUBCAT_MAP:
        if kw in msg_norm:
            cat_hint = f'\nÖNEMLİ: Kullanıcı "{kw}" istiyor. ÖNERİLERİ SADECE "{subcat_norm.upper()}" kategorisinden seç.'
            break

    system = f"""Sen Loss Cafe'de çalışan samimi bir garson gibisin. Normal konuş.
MENÜ:
{menu_text}
{cat_hint}
ÖNERİLER, liste, köşeli parantez [ ] ASLA yazma. Sadece konuş.
"""
    messages = [{"role":"system","content":system}]
    for h in history[-8:]:
        messages.append({"role":h.get("role","user"),"content":h.get("content","")[:350]})
    if prev_msg:
        messages.append({"role":"user","content":prev_msg[:150]})
        messages.append({"role":"assistant","content":"[Önceki öneri verildi]"})
    messages.append({"role":"user","content":user_msg})

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=350,
        temperature=0.4,
    )
    text = (resp.choices[0].message.content or '').strip()
    suggestions = []

    if "ÖNERİLER:" in text:
        parts = text.split("ÖNERİLER:")
        text = parts[0].strip()
        try:
            json_str = parts[1].strip().strip("[]")
            names = json.loads("[" + json_str + "]") if json_str else []
            for n in names[:8]:
                name = (n if isinstance(n,str) else str(n)).strip()
                for i in items:
                    if name.lower() in (i.get("name") or '').lower():
                        suggestions.append(i)
                        break
        except Exception:
            pass

    if suggestions and cat_hint:
        for kw, subcat_norm in MENU_SUBCAT_MAP:
            if kw in msg_norm:
                filtered = [i for i in suggestions if subcat_norm in _normalize(i.get('subcategory') or '')]
                if filtered:
                    suggestions = filtered[:8]
                break

    return {"success": True, "greeting": False, "message": text, "suggestions": suggestions}

# ---------------------
# Django API Views
# ---------------------
def _api_response(data):
    r = JsonResponse(data)
    r['Access-Control-Allow-Origin'] = '*'
    return r

@require_GET
@cache_page(60*5)
def api_menu_full(request):
    lang = (request.GET.get('lang') or 'tr').lower()
    if not lang.startswith('en'):
        lang = 'tr'
    else:
        lang = 'en'
    return _api_response({'success': True, 'menu': _build_menu_tree(request, lang=lang)})

@require_GET
@cache_page(60*5)
def api_menu_flat(request):
    lang = (request.GET.get('lang') or 'tr').lower()
    if not lang.startswith('en'):
        lang = 'tr'
    else:
        lang = 'en'
    return _api_response({'success': True, 'items': _build_flat_menu(request, lang=lang)})


@require_GET
def api_test_groq(request):
    """
    Basit sağlık kontrolü / Groq entegrasyon testi için endpoint.
    Frontend veya Postman ile hızlı test yapabilmek için.
    """
    has_key = bool((os.environ.get('GROQ_API_KEY') or '').strip())
    return _api_response({
        'success': True,
        'groq_configured': has_key,
    })

@csrf_exempt
@require_POST
def api_chat_suggest(request):
    try:
        body = json.loads(request.body or '{}')
        msg = (body.get('message') or '').strip()
        prev = (body.get('previous_message') or '').strip()
    except json.JSONDecodeError:
        msg = ''
        prev = ''

    api_key = (os.environ.get('GROQ_API_KEY') or '').strip()
    history = body.get('history', [])

    if api_key:
        try:
            result = _ai_chat(msg, prev, history, api_key)
            sugs = result.get('suggestions', [])[:8]
            if not sugs and msg.strip() and _extract_keywords(msg):
                db_sugs, _ = _get_chat_suggestions(msg)
                if db_sugs:
                    return _api_response({'success': True, 'greeting': False,
                                          'message': result.get('message','İşte size önerilerimiz:'),
                                          'suggestions': db_sugs[:8]})
            return _api_response({'success': True,
                                  'greeting': result.get('greeting', False),
                                  'message': result.get('message','Size nasıl yardımcı olabilirim?'),
                                  'suggestions': sugs})
        except Exception as e:
            logger.warning("Groq hatası: %s", str(e))

    amb = _check_ambiguity(msg)
    if amb:
        return _api_response({
            'success': True,
            'clarification': amb['question'],
            'options': [opt[0] for opt in amb['options']],
            'option_hints': [opt[1] for opt in amb['options']],
            'suggestions': [],
        })

    suggestions, _ = _get_chat_suggestions(msg)
    msg_text = 'İşte size önerilerimiz:' if suggestions else 'Ne yemek veya içmek istersiniz? Menüden size önerebilirim 😊'
    return _api_response({'success': True, 'greeting': not bool(suggestions),
                          'message': msg_text, 'suggestions': suggestions[:8]})
