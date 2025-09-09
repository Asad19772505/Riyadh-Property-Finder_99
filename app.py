"""
Riyadh Apartment Finder – API Stub Version (Streamlit)
-----------------------------------------------------
Single‑file Streamlit app with:
  • Bilingual UI (Arabic/English)
  • CSV uploads + templates (Aqar, Bayut, Property Finder, Haraj, Generic)
  • WhatsApp contact button per listing (uses `contact_phone` column or sidebar fallback)
  • **API integration stubs** for Bayut and Property Finder (placeholders you can later wire to real partner APIs)

Run:
    streamlit run app_api_stubs.py

Requirements (minimal):
    streamlit, pandas, numpy
Optional (for real API calls later):
    requests, python-dotenv

⚠️ Important: Many marketplaces prohibit scraping and restrict API access to partners.
Use official, documented endpoints and respect each provider's Terms of Service.
"""
from __future__ import annotations
import ast
import json
import re
import textwrap
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import streamlit as st

# If you plan to call partner APIs later, uncomment the two lines below
# import requests
# from requests import Session

# =============================
# Language & District Mappings
# =============================
LANGS = ["English", "العربية"]

DISTRICT_MAP_EN_TO_AR = {
    "Al Murooj": "المروج",
    "Al Maseef": "المسيـف",
    "Al Nakheel": "النخيل",
    "Al Malqa": "الملقا",
    "Hittin": "حطين",
    "Al Sahafa": "الصحافة",
    "Al Wurud": "الورود",
    "Al Ghadir": "الغدير",
    "Al Andalus": "الأندلس",
    "Al Narjis": "النرجس",
    "Al Rabi": "الربيع",
    "Al Olaya": "العليا",
    "Al Arid": "العريض",
    "Al Murabba": "المربع",
    "Qurtubah": "قرطبة",
    "Al Yarmouk": "اليرموك",
    "Al Hamra": "الحمراء",
}
DISTRICTS_EN = list(DISTRICT_MAP_EN_TO_AR.keys())
DISTRICT_MAP_AR_TO_EN = {v: k for k, v in DISTRICT_MAP_EN_TO_AR.items()}

# Approximate district centroids (for plotting when lat/lon not provided)
DISTRICT_CENTROIDS = {
    "Al Murooj": (24.7492, 46.6768),
    "Al Maseef": (24.7466, 46.6394),
    "Al Nakheel": (24.7400, 46.6500),
    "Al Malqa": (24.8075, 46.6260),
    "Hittin": (24.7778, 46.5900),
    "Al Sahafa": (24.8080, 46.6400),
    "Al Wurud": (24.7090, 46.6760),
    "Al Narjis": (24.8820, 46.6630),
}

# =============================
# UI Text (i18n)
# =============================
UI = {
    "title": {"English": "Riyadh Apartment Finder – API Stub Version", "العربية": "باحث شقق الرياض – نسخة واجهات برمجية (تجريبية)"},
    "caption": {
        "English": "Filter apartments, upload CSVs, and prepare for partner APIs (Bayut/Property Finder).",
        "العربية": "صفِّ الشقق، ارفع ملفات CSV، وجهّز للتكامل مع واجهات الشركاء (بيوت/بروبرتي فايندر).",
    },
    "language": {"English": "Language", "العربية": "اللغة"},
    "providers": {"English": "Data Providers", "العربية": "مصادر البيانات"},
    "dummy": {"English": "Dummy data (testing)", "العربية": "بيانات تجريبية"},
    "uploads": {"English": "CSV Uploads", "العربية": "رفع CSV"},
    "upload_tip": {"English": "Use templates below to prepare provider CSVs.", "العربية": "استخدم القوالب أدناه لتجهيز CSV لكل منصة."},
    "filters": {"English": "Filters", "العربية": "فلاتر"},
    "purpose": {"English": "Purpose", "العربية": "الغرض"},
    "rent": {"English": "Rent", "العربية": "إيجار"},
    "sale": {"English": "Sale", "العربية": "بيع"},
    "districts": {"English": "Districts", "العربية": "الأحياء"},
    "price_range": {"English": "Price range (SAR)", "العربية": "نطاق السعر (ر.س)"},
    "bedrooms": {"English": "Bedrooms", "العربية": "غرف نوم"},
    "size": {"English": "Size (sqm)", "العربية": "المساحة (م²)"},
    "furnished": {"English": "Furnished?", "العربية": "مفروشة؟"},
    "any": {"English": "Any", "العربية": "أي"},
    "furnished_yes": {"English": "Furnished", "العربية": "مفروشة"},
    "furnished_no": {"English": "غير مفروشة", "العربية": "غير مفروشة"},
    "sort": {"English": "Sort by", "العربية": "ترتيب حسب"},
    "newest": {"English": "Newest", "العربية": "الأحدث"},
    "price_lh": {"English": "Price (low→high)", "العربية": "السعر (من الأقل إلى الأعلى)"},
    "price_hl": {"English": "Price (high→low)", "العربية": "السعر (من الأعلى إلى الأقل)"},
    "size_ls": {"English": "Size (large→small)", "العربية": "المساحة (كبيرة → صغيرة)"},
    "summary": {"English": "Summary", "العربية": "ملخص"},
    "listings_found": {"English": "Listings found", "العربية": "العروض المتاحة"},
    "median_price": {"English": "Median price (SAR)", "العربية": "السعر الوسيط (ر.س)"},
    "median_pps": {"English": "Median SAR/sqm", "العربية": "الوسيط ر.س/م²"},
    "map": {"English": "Map of Listings", "العربية": "خريطة العروض"},
    "results": {"English": "Results", "العربية": "النتائج"},
    "provider": {"English": "Provider", "العربية": "المنصة"},
    "open": {"English": "Open listing", "العربية": "فتح العرض"},
    "save": {"English": "Save to shortlist", "العربية": "حفظ في المفضلة"},
    "added": {"English": "Added to shortlist", "العربية": "تمت الإضافة"},
    "shortlist": {"English": "Shortlist", "العربية": "المفضلة"},
    "no_shortlist": {"English": "No items saved yet.", "العربية": "لا يوجد عناصر بعد."},
    "no_coords": {"English": "No coordinates available yet.", "العربية": "لا توجد إحداثيات حالياً."},
    "templates": {"English": "CSV Templates", "العربية": "قوالب CSV"},
    "whats_defaults": {"English": "WhatsApp defaults", "العربية": "إعدادات واتساب"},
    "whats_phone": {"English": "Default WhatsApp phone (+966…)", "العربية": "رقم واتساب الافتراضي (+966…)"},
    "whats_msg": {"English": "Message template", "العربية": "قالب الرسالة"},
    "whats_button": {"English": "WhatsApp agent", "العربية": "مراسلة واتساب"},
    "apis": {"English": "API Integrations (stubs)", "العربية": "تكاملات API (تجريبية)"},
    "bayut_enable": {"English": "Enable Bayut API (stub)", "العربية": "تفعيل API بيوت (تجريبي)"},
    "pf_enable": {"English": "Enable Property Finder API (stub)", "العربية": "تفعيل API بروبرتي فايندر (تجريبي)"},
    "api_note": {"English": "Provide partner credentials/endpoints if you have access.", "العربية": "أدخل بيانات الشريك ونقاط النهاية إذا كان لديك صلاحية."},
}

def T(key: str, lang: str) -> str:
    return UI.get(key, {}).get(lang, key)

# =============================
# Normalized Schema (contact_phone included for WhatsApp)
# =============================
@dataclass
class Listing:
    provider: str
    listing_id: str
    title: str
    price_sar: Optional[float]
    price_period: Optional[str]
    bedrooms: Optional[float]
    bathrooms: Optional[float]
    size_sqm: Optional[float]
    furnished: Optional[bool]
    district: Optional[str]
    city: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    url: Optional[str]
    images: Optional[List[str]]
    description: Optional[str]
    date_posted: Optional[str]
    contact_phone: Optional[str]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Listing":
        def to_bool(x):
            if pd.isna(x): return None
            if isinstance(x, bool): return x
            s = str(x).strip().lower()
            if s in {"true","yes","y","1","furnished","مفروشة"}: return True
            if s in {"false","no","n","0","unfurnished","غير مفروشة"}: return False
            return None

        def to_list_imgs(x):
            if pd.isna(x): return None
            if isinstance(x, list): return x
            s = str(x).strip()
            try:
                val = ast.literal_eval(s)
                if isinstance(val, list):
                    return [str(u) for u in val]
            except Exception:
                pass
            return [s] if s else None

        def to_float(x):
            try:
                if pd.isna(x) or x == "": return None
                return float(str(x).replace(",", "").strip())
            except Exception:
                return None

        def to_str(x):
            if pd.isna(x): return None
            s = str(x).strip()
            return s if s else None

        def norm_district(x):
            s = to_str(x)
            if not s: return None
            if s in DISTRICT_MAP_AR_TO_EN: return DISTRICT_MAP_AR_TO_EN[s]
            return s

        def coord_lat(x):
            v = to_float(x)
            if v is None or not (-90 <= v <= 90): return None
            return v

        def coord_lon(x):
            v = to_float(x)
            if v is None or not (-180 <= v <= 180): return None
            return v

        return Listing(
            provider=to_str(d.get("provider")) or "unknown",
            listing_id=to_str(d.get("listing_id")) or str(hash(json.dumps(d, sort_keys=True))),
            title=to_str(d.get("title")) or "Apartment",
            price_sar=to_float(d.get("price_sar")),
            price_period=to_str(d.get("price_period")),
            bedrooms=to_float(d.get("bedrooms")),
            bathrooms=to_float(d.get("bathrooms")),
            size_sqm=to_float(d.get("size_sqm")),
            furnished=to_bool(d.get("furnished")),
            district=norm_district(d.get("district")),
            city=to_str(d.get("city")) or "Riyadh",
            latitude=coord_lat(d.get("latitude")),
            longitude=coord_lon(d.get("longitude")),
            url=to_str(d.get("url")),
            images=to_list_imgs(d.get("images")),
            description=to_str(d.get("description")),
            date_posted=to_str(d.get("date_posted")),
            contact_phone=to_str(d.get("contact_phone")),
        )

# =============================
# Page setup
# =============================
st.set_page_config(page_title="Riyadh Apartment Finder – API Stubs", layout="wide", page_icon="🏙️")
with st.sidebar:
    lang = st.selectbox(T("language", "English"), LANGS, index=0)

st.title(T("title", lang))
st.caption(T("caption", lang))

# =============================
# Providers & CSV Templates
# =============================
with st.sidebar:
    st.header(T("providers", lang))
    use_dummy = st.checkbox(T("dummy", lang), value=True)
    st.divider()
    st.subheader(T("uploads", lang))
    aqar_csv = st.file_uploader("Aqar CSV", type=["csv"], key="aqar")
    bayut_csv = st.file_uploader("Bayut CSV", type=["csv"], key="bayut")
    pf_csv = st.file_uploader("Property Finder CSV", type=["csv"], key="pf")
    haraj_csv = st.file_uploader("Haraj CSV", type=["csv"], key="haraj")
    st.caption(T("upload_tip", lang))

st.subheader(T("templates", lang))
TEMPLATE_COLUMNS = [
    "provider","listing_id","title","price_sar","price_period","bedrooms","bathrooms",
    "size_sqm","furnished","district","city","latitude","longitude","url","images",
    "description","date_posted","contact_phone"
]

def make_template(provider: str) -> bytes:
    df = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    df.loc[0] = [provider, "", "", "", "monthly", "", "", "", "", "Al Murooj", "Riyadh", "", "", "", "", "", datetime.now().date().isoformat(), "+9665XXXXXXXX"]
    return df.to_csv(index=False).encode("utf-8")

cA, cB, cC, cD, cE = st.columns(5)
with cA: st.download_button("Generic Aggregator CSV", data=make_template("generic"), file_name="template_generic.csv")
with cB: st.download_button("Aqar CSV", data=make_template("aqar"), file_name="template_aqar.csv")
with cC: st.download_button("Bayut CSV", data=make_template("bayut"), file_name="template_bayut.csv")
with cD: st.download_button("PropertyFinder CSV", data=make_template("property_finder"), file_name="template_property_finder.csv")
with cE: st.download_button("Haraj CSV", data=make_template("haraj"), file_name="template_haraj.csv")

# =============================
# Normalization helpers
# =============================
@st.cache_data(show_spinner=False)
def _normalize_df(df: pd.DataFrame, provider_name: str) -> pd.DataFrame:
    col_map = {
        "provider": ["provider","source","المصدر"],
        "listing_id": ["listing_id","id","ref","reference","المرجع"],
        "title": ["title","name","headline","العنوان"],
        "price_sar": ["price_sar","price","rent","amount","السعر"],
        "price_period": ["price_period","period","tenure","التسعير"],
        "bedrooms": ["bedrooms","beds","br","غرف"],
        "bathrooms": ["bathrooms","baths","ba","حمامات"],
        "size_sqm": ["size_sqm","area","area_sqm","size","المساحة"],
        "furnished": ["furnished","is_furnished","furnish","التجهيز"],
        "district": ["district","area_name","neighborhood","suburb","الحي"],
        "city": ["city","المدينة"],
        "latitude": ["latitude","lat","خط العرض"],
        "longitude": ["longitude","lon","lng","long","خط الطول"],
        "url": ["url","link","الرابط"],
        "images": ["images","image","photo_urls","الصور"],
        "description": ["description","desc","details","الوصف"],
        "date_posted": ["date_posted","posted","date","created_at","تاريخ النشر"],
        "contact_phone": ["contact_phone","phone","mobile","whatsapp","رقم الاتصال","جوال","واتساب"],
    }

    def pick(colnames, opts):
        for c in opts:
            if c in colnames:
                return c
        return None

    canon = {k: pick(df.columns, opts) for k, opts in col_map.items()}

    rows = []
    for _, r in df.iterrows():
        nd = {}
        for k, c in canon.items():
            nd[k] = r[c] if c in df.columns else None
        nd["provider"] = nd.get("provider") or provider_name
        rows.append(asdict(Listing.from_dict(nd)))

    ndf = pd.DataFrame(rows)

    for i, row in ndf.iterrows():
        if (pd.isna(row["latitude"]) or pd.isna(row["longitude"])) and row["district"] in DISTRICT_CENTROIDS:
            lat, lon = DISTRICT_CENTROIDS[row["district"]]
            ndf.at[i, "latitude"] = lat
            ndf.at[i, "longitude"] = lon

    return ndf


def provider_from_csv(name: str, file) -> pd.DataFrame:
    df = pd.read_csv(file)
    return _normalize_df(df, provider_name=name)


def provider_dummy(districts_en: List[str], n: int = 40, for_rent: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(17)
    choices = districts_en or DISTRICTS_EN[:6]
    rows = []
    for i in range(n):
        d_en = rng.choice(choices)
        lat, lon = DISTRICT_CENTROIDS.get(d_en, (24.7136, 46.6753))
        price = int(rng.uniform(3500, 16000)) if for_rent else int(rng.uniform(450000, 2500000))
        period = "monthly" if for_rent else None
        br = int(rng.integers(1, 6))
        ba = max(1, br - 1)
        size = int(rng.uniform(70, 250))
        furnished = bool(rng.integers(0, 2))
        phone = "+9665" + str(rng.integers(10000000, 99999999))
        rows.append(asdict(Listing(
            provider="dummy",
            listing_id=f"D-{i}",
            title=f"{br}BR Apartment in {d_en}",
            price_sar=price,
            price_period=period,
            bedrooms=br,
            bathrooms=ba,
            size_sqm=size,
            furnished=furnished,
            district=d_en,
            city="Riyadh",
            latitude=lat + rng.normal(scale=0.003),
            longitude=lon + rng.normal(scale=0.003),
            url=None,
            images=None,
            description=f"Spacious {br}BR, {size} sqm in {d_en}.",
            date_posted=datetime.now().date().isoformat(),
            contact_phone=phone,
        )))
    return pd.DataFrame(rows)

# =============================
# API Integration Stubs (placeholders)
# =============================
@st.cache_data(show_spinner=False)
def bayut_api_stub(base_url: str, api_key: str, params: Dict[str, Any]) -> pd.DataFrame:
    """Placeholder for Bayut partner API.
    Expected to return a DataFrame in the normalized schema. For now, we just
    return an empty DataFrame with the proper columns.

    Example future call:
        url = f"{base_url.rstrip('/')}/listings"
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        # TODO: map payload fields -> normalized schema rows
    """
    return pd.DataFrame(columns=TEMPLATE_COLUMNS)


@st.cache_data(show_spinner=False)
def property_finder_api_stub(base_url: str, client_id: str, client_secret: str, params: Dict[str, Any]) -> pd.DataFrame:
    """Placeholder for Property Finder partner API.
    If an OAuth token is required, first exchange client credentials for an access token,
    then call the listings endpoint and map to the normalized schema.

    Example future call:
        token_url = f"{base_url.rstrip('/')}/oauth/token"
        token = requests.post(token_url, data={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}).json()["access_token"]
        url = f"{base_url.rstrip('/')}/listings"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
        payload = resp.json()
        # TODO: map payload -> normalized rows
    """
    return pd.DataFrame(columns=TEMPLATE_COLUMNS)

# =============================
# Filters + WhatsApp defaults + API settings
# =============================
with st.sidebar:
    st.header(T("filters", lang))
    purpose = st.radio(T("purpose", lang), [T("rent", lang), T("sale", lang)], horizontal=True)

    if lang == "العربية":
        default_ar = [DISTRICT_MAP_EN_TO_AR.get("Al Murooj"), DISTRICT_MAP_EN_TO_AR.get("Al Maseef")]
        districts_shown = [DISTRICT_MAP_EN_TO_AR.get(d, d) for d in DISTRICTS_EN]
        selected_ar = st.multiselect(T("districts", lang), districts_shown, default=default_ar)
        selected_en = [DISTRICT_MAP_AR_TO_EN.get(x, x) for x in selected_ar]
    else:
        selected_en = st.multiselect(T("districts", lang), DISTRICTS_EN, default=["Al Murooj","Al Maseef"])

    min_price, max_price = st.slider(T("price_range", lang), 1000, 3000000, (3000, 15000) if purpose==T("rent", lang) else (300000, 2000000), step=1000)
    br_min, br_max = st.slider(T("bedrooms", lang), 0, 7, (2, 5))
    size_min, size_max = st.slider(T("size", lang), 0, 1200, (80, 300))
    furn_choice = st.selectbox(T("furnished", lang), [T("any", lang), T("furnished_yes", lang), T("furnished_no", lang)])
    sort_by = st.selectbox(T("sort", lang), [T("newest", lang), T("price_lh", lang), T("price_hl", lang), T("size_ls", lang)])

    st.divider()
    st.subheader(T("whats_defaults", lang))
    default_phone = st.text_input(T("whats_phone", lang), value="+9665XXXXXXXX", help="Used if a listing has no contact_phone column.")
    default_msg_template = st.text_area(
        T("whats_msg", lang),
        value=(
            "Hello, I'm interested in this apartment: {title} in {district}. "
            "Price: {price} {period}. Link: {url}"
        ),
        height=70,
        help="Available placeholders: {title}, {district}, {price}, {period}, {url}"
    )

    st.divider()
    st.subheader(T("apis", lang))
    st.caption(T("api_note", lang))

    # Bayut stub controls
    bayut_enabled = st.checkbox(T("bayut_enable", lang), value=False)
    bayut_base = st.text_input("Bayut Base URL", value="https://api.bayut.sa")
    bayut_key = st.text_input("Bayut API Key", type="password")

    # Property Finder stub controls
    pf_enabled = st.checkbox(T("pf_enable", lang), value=False)
    pf_base = st.text_input("Property Finder Base URL", value="https://api.propertyfinder.sa")
    pf_client_id = st.text_input("PF Client ID")
    pf_client_secret = st.text_input("PF Client Secret", type="password")

# =============================
# Ingest data
# =============================
frames: List[pd.DataFrame] = []

# Dummy data
if use_dummy:
    frames.append(provider_dummy(selected_en, n=40, for_rent=(purpose==T("rent", lang))))

# CSV uploads
if aqar_csv is not None:
    frames.append(provider_from_csv("aqar", aqar_csv))
if bayut_csv is not None:
    frames.append(provider_from_csv("bayut", bayut_csv))
if pf_csv is not None:
    frames.append(provider_from_csv("property_finder", pf_csv))
if haraj_csv is not None:
    frames.append(provider_from_csv("haraj", haraj_csv))

# API stubs (currently return empty frames with normalized columns)
api_params = {
    "districts": selected_en,
    "purpose": "rent" if purpose==T("rent", lang) else "sale",
    "min_price": min_price,
    "max_price": max_price,
    "bedrooms_min": br_min,
    "bedrooms_max": br_max,
}

if bayut_enabled and bayut_base and bayut_key:
    frames.append(bayut_api_stub(bayut_base, bayut_key, api_params))

if pf_enabled and pf_base and pf_client_id and pf_client_secret:
    frames.append(property_finder_api_stub(pf_base, pf_client_id, pf_client_secret, api_params))

# Combine
if frames:
    data = pd.concat(frames, ignore_index=True, sort=False)
else:
    data = pd.DataFrame(columns=TEMPLATE_COLUMNS)

# Purpose filter (rent vs sale) using price_period
if purpose == T("rent", lang):
    data = data[(data["price_period"].astype(str).str.lower() == "monthly") | (data["price_period"].astype(str).str.lower() == "yearly") | (data["price_period"].isna())]
else:
    data = data[data["price_period"].isna()]

# District filter
if selected_en:
    data = data[data["district"].isin(selected_en)]

# Numeric filters
between = lambda s, lo, hi: pd.to_numeric(s, errors="coerce").fillna(-1e15).between(lo, hi)
data = data[between(data["price_sar"], min_price, max_price)]
data = data[(pd.to_numeric(data["bedrooms"], errors="coerce").fillna(br_min) >= br_min) & (pd.to_numeric(data["bedrooms"], errors="coerce").fillna(br_max) <= br_max)]
data = data[between(data["size_sqm"], size_min, size_max)]

if furn_choice != T("any", lang):
    want = (furn_choice == T("furnished_yes", lang))
    data = data[data["furnished"].fillna(False) == want]

# Sorting
if sort_by == T("newest", lang):
    def parse_date(x):
        for fmt in ("%Y-%m-%d","%d-%m-%Y","%d/%m/%Y","%Y/%m/%d","%Y-%m-%d %H:%M:%S"):
            try: return datetime.strptime(str(x), fmt)
            except Exception: continue
        return datetime.min
    data["_parsed_date"] = data["date_posted"].apply(parse_date)
    data = data.sort_values("_parsed_date", ascending=False)
elif sort_by == T("price_lh", lang):
    data = data.sort_values(pd.to_numeric(data["price_sar"], errors="coerce"), ascending=True, na_position="last")
elif sort_by == T("price_hl", lang):
    data = data.sort_values(pd.to_numeric(data["price_sar"], errors="coerce"), ascending=False, na_position="last")
elif sort_by == T("size_ls", lang):
    data = data.sort_values(pd.to_numeric(data["size_sqm"], errors="coerce"), ascending=False, na_position="last")

# Deduplicate
if not data.empty:
    key1 = data["provider"].fillna("") + "|" + data["listing_id"].fillna("")
    key2 = data["title"].fillna("") + "|" + data["district"].fillna("") + "|" + data["price_sar"].fillna(-1).astype(str)
    data = data.loc[~key1.duplicated(keep="first")]
    data = data.loc[~key2.duplicated(keep="first")]

# =============================
# WhatsApp helpers
# =============================
PHONE_DIGITS = re.compile(r"\D+")

def clean_phone(phone: Optional[str]) -> Optional[str]:
    if not phone: return None
    digits = PHONE_DIGITS.sub("", str(phone))
    if not digits: return None
    # If user typed leading 0 (e.g., 05xxxxxxxx), convert -> 9665xxxxxxxx
    if digits.startswith("0") and len(digits) >= 9:
        digits = "966" + digits.lstrip("0")
    # If no country code and looks like KSA mobile length, prepend 966
    if len(digits) in (9,10) and not digits.startswith("966"):
        digits = "966" + digits[-9:]
    return digits

def build_whatsapp_link(phone: str, title: str, district_label: str, price: str, period: str, url: Optional[str], template: str) -> str:
    msg = template.format(title=title, district=district_label, price=price, period=period, url=url or "")
    return f"https://wa.me/{phone}?text={urllib.parse.quote_plus(msg)}"

# =============================
# Summary & Map
# =============================
left, right = st.columns([1, 2])
with left:
    st.subheader(T("summary", lang))
    st.metric(T("listings_found", lang), len(data))
    if len(data):
        med_price_series = pd.to_numeric(data["price_sar"], errors="coerce")
        med_price = int(np.nanmedian(med_price_series)) if not med_price_series.dropna().empty else 0
        st.metric(T("median_price", lang), med_price)
        pps = (pd.to_numeric(data["price_sar"], errors="coerce") / pd.to_numeric(data["size_sqm"], errors="coerce")).replace([np.inf,-np.inf], np.nan)
        pps_med = int(np.nanmedian(pps)) if not pps.dropna().empty else 0
        st.metric(T("median_pps", lang), pps_med)
with right:
    st.subheader(T("map", lang))
    map_df = data.dropna(subset=["latitude","longitude"]).copy()
    if map_df.empty:
        st.info(T("no_coords", lang))
    else:
        st.map(map_df[["latitude","longitude"]], size=16)

# =============================
# Results grid
# =============================
st.subheader(T("results", lang))

if data.empty:
    st.warning("No listings match filters.")
else:
    if "shortlist" not in st.session_state:
        st.session_state["shortlist"] = []

    for i, row in data.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1,3,1])
            with c1:
                if isinstance(row.get("images"), list) and row["images"]:
                    st.image(row["images"][0], use_container_width=True)
                else:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg", use_container_width=True)
            with c2:
                d_en = row.get("district")
                d_label = DISTRICT_MAP_EN_TO_AR.get(d_en, d_en) if lang == "العربية" else d_en
                title = row.get("title") or "Apartment"
                subtitle = f"{d_label or '—'}, {row.get('city') or 'Riyadh'}"
                st.markdown(f"### {title}")
                st.caption(subtitle)

                price_val = row.get("price_sar")
                price_str = f"{int(float(price_val)):,} SAR" if pd.notna(price_val) and str(price_val) != "" else ("—" if lang=="العربية" else "Price on request")
                period = row.get("price_period") or ("monthly" if purpose==T("rent", lang) else "")
                if isinstance(row.get("price_period"), str):
                    price_disp = f"{price_str} / {row['price_period']}"
                else:
                    price_disp = price_str

                specs = [
                    f"🛏️ {int(row['bedrooms']) if pd.notna(row['bedrooms']) else '?'} BR",
                    f"🛁 {int(row['bathrooms']) if pd.notna(row['bathrooms']) else '?'} BA",
                    f"📐 {int(row['size_sqm']) if pd.notna(row['size_sqm']) else '?'} sqm",
                    f"🪑 {'Furnished' if row['furnished'] else 'Unfurnished' if row['furnished'] is not None else '—'}",
                ]
                st.markdown(f"**{price_disp}**  ·  " + "  ·  ".join(specs))

                if row.get("description"):
                    st.write(textwrap.shorten(str(row["description"]), width=220, placeholder="…"))
            with c3:
                st.markdown(f"**{T('provider', lang)}:** {row.get('provider')}")
                if row.get("url"):
                    st.link_button(T("open", lang), row["url"], use_container_width=True)

                # WhatsApp button
                phone_raw = row.get("contact_phone") or default_phone
                phone = clean_phone(phone_raw)
                if phone:
                    wa_link = build_whatsapp_link(
                        phone=phone,
                        title=title,
                        district_label=d_label or (row.get("district") or "Riyadh"),
                        price=price_str,
                        period=period or "",
                        url=row.get("url"),
                        template=default_msg_template,
                    )
                    st.link_button("📲 " + T("whats_button", lang), wa_link, use_container_width=True)
                else:
                    st.caption("Add a valid WhatsApp number to enable quick contact.")

                if st.button("➕ " + T("save", lang), key=f"save_{i}"):
                    st.session_state["shortlist"].append(row.to_dict())
                    st.success(T("added", lang))

    st.divider()
    st.subheader(T("shortlist", lang))
    if st.session_state["shortlist"]:
        shortlist_df = pd.DataFrame(st.session_state["shortlist"])  # type: ignore
        st.dataframe(shortlist_df, use_container_width=True)
        csv = shortlist_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download shortlist (CSV)", data=csv, file_name="shortlist_riyadh.csv")
    else:
        st.caption(T("no_shortlist", lang))

# =============================
# Developer Notes
# =============================
st.divider()
st.subheader("Developer Notes – Wiring Real APIs")
st.markdown(
    """
    **Bayut (partner)**
    - Replace `bayut_api_stub` with a real implementation.
    - Add authentication (Bearer token) and map the payload to the normalized schema.

    **Property Finder (partner)**
    - Replace `property_finder_api_stub` with a real implementation.
    - If OAuth2 is required, obtain an access token first.

    **General mapping tips**
    - Always populate: `provider, listing_id, title, price_sar, price_period, bedrooms, bathrooms, size_sqm, furnished, district, city, latitude, longitude, url, images, description, date_posted, contact_phone`.
    - If coordinates are missing but district exists, we fallback to centroids for map visualization.

    **Compliance**
    - Use only official/approved endpoints and follow each provider's ToS.
    - Avoid scraping; negotiate partner access where possible.
    """
)
