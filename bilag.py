import streamlit as st
import requests
from PIL import Image
import io
import base64
import hashlib
from datetime import date
from difflib import SequenceMatcher

try:
    import anthropic
except ImportError:
    anthropic = None

st.set_page_config(
    page_title="E-conomic Bilag",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container { padding-top: 1.2rem; padding-bottom: 4rem; max-width: 760px; }
        h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, "SF Pro", sans-serif; color: #1d1d1f; font-weight: 600; }
        h1 { text-align: center; font-size: 1.7rem; margin-bottom: 0.2rem; }
        h3 { font-size: 0.95rem; color: #86868b; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 1.4rem; }
        .stButton>button { border-radius: 12px; background-color: #0071e3; color: white; border: none; font-weight: 500; padding: 10px 20px; width: 100%; }
        .stButton>button:hover { background-color: #0077ed; color: white; }
        div[data-testid="stExpander"] { background-color: white; border-radius: 12px; border: 1px solid #e5e5ea; }
        div[data-testid="stRadio"] > div { background-color: white; padding: 8px 14px; border-radius: 12px; border: 1px solid #e5e5ea; }
        div[data-testid="stSelectbox"] > div > div { background-color: white; border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; background: #f5f5f7; }
        .stTabs [aria-selected="true"] { background: #0071e3 !important; color: white !important; }
        .match-card { background: white; border: 1px solid #e5e5ea; border-radius: 12px; padding: 14px; margin-bottom: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Bilag → e-conomic")
st.caption("Skan bilag · AI udtrækker data · matcher mod kladde-posteringer")

BASE_URL = "https://restapi.e-conomic.com"

MODELS = {
    "Hurtig (Haiku 4.5)": "claude-haiku-4-5-20251001",
    "Robust (Sonnet 4.6)": "claude-sonnet-4-6",
}

EXTRACT_TOOL = {
    "name": "extract_receipt",
    "description": "Udtræk strukturerede data fra et bilag/kvittering/faktura.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": ["string", "null"],
                "description": "Transaktionsdato i ISO-format YYYY-MM-DD",
            },
            "total_amount": {
                "type": "number",
                "description": "Totalbeløb inkl. moms, positivt tal",
            },
            "vat_amount": {
                "type": ["number", "null"],
                "description": "Momsbeløb hvis vist separat",
            },
            "currency": {
                "type": "string",
                "description": "ISO valutakode (DKK, EUR, USD osv.)",
            },
            "vendor": {
                "type": "string",
                "description": "Forretningens/leverandørens navn",
            },
            "invoice_number": {"type": ["string", "null"]},
            "description": {
                "type": "string",
                "description": "Kort beskrivelse på 1-5 ord (fx 'Frokost', 'Brændstof', 'Software-abonnement')",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Hvor tydeligt og pålideligt udtrækket er",
            },
        },
        "required": ["total_amount", "currency", "vendor", "description", "confidence"],
    },
    "cache_control": {"type": "ephemeral"},
}

SYSTEM_PROMPT = """Du er ekspert i at udtrække strukturerede data fra danske bilag (kvitteringer, fakturaer, regninger).

Udtræk præcise oplysninger fra billedet:
- Dato (ISO-format YYYY-MM-DD)
- Totalbeløb inkl. moms (punktum som decimaltegn)
- Momsbeløb hvis vist separat
- Valuta (DKK som default for danske bilag)
- Leverandørens/forretningens navn
- Faktura- eller bonsnummer hvis synligt
- Kort beskrivelse på 1-5 ord af hvad der er købt
- Konfidens (high/medium/low) baseret på hvor tydeligt bilaget er læseligt

Kald altid extract_receipt-værktøjet. Sæt felter til null hellere end at gætte hvis du ikke kan læse dem klart."""


def _secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


def _secrets_section(key):
    try:
        v = st.secrets[key]
        return dict(v) if v else {}
    except Exception:
        return {}


# ----- Sidebar -----
with st.sidebar:
    st.subheader("E-conomic aftale")

    agreements = _secrets_section("agreements")
    if agreements:
        agreement_name = st.selectbox(
            f"Vælg blandt {len(agreements)} aftaler",
            options=list(agreements.keys()),
            key="_agreement_select",
        )
        grant_token = agreements[agreement_name]
    else:
        st.caption("Ingen aftaler i secrets — indtast manuelt")
        agreement_name = "Manuel"
        grant_token = st.text_input(
            "Agreement Grant Token", type="password", key="_grant_manual"
        )

    app_secret = _secret("ECONOMIC_APP_SECRET") or st.text_input(
        "App Secret Token", type="password", key="_app_secret"
    )

    st.divider()
    st.subheader("AI-analyse")
    model_label = st.radio(
        "Model", options=list(MODELS.keys()), index=0, key="_model_select"
    )
    model_id = MODELS[model_label]
    anthropic_key = _secret("ANTHROPIC_API_KEY") or st.text_input(
        "Anthropic API key", type="password", key="_anth_key"
    )

if not app_secret or not grant_token:
    st.info("Sæt e-conomic tokens i sidebaren (☰).")
    st.stop()

if anthropic is None:
    st.error("Pakken `anthropic` mangler. Tilføj til requirements.txt og redeploy.")
    st.stop()

HEADERS = {
    "X-AppSecretToken": app_secret,
    "X-AgreementGrantToken": grant_token,
    "Content-Type": "application/json",
}


@st.cache_data(ttl=60, show_spinner=False)
def api_get(endpoint, h_tuple):
    headers = dict(h_tuple)
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def h_tuple():
    return tuple(sorted(HEADERS.items()))


def upload_attachment(journal_no, ay, vn, pdf_bytes):
    url = f"{BASE_URL}/journals/{journal_no}/vouchers/{ay}-{vn}/attachment/file"
    h = {
        "X-AppSecretToken": app_secret,
        "X-AgreementGrantToken": grant_token,
        "Content-Type": "application/pdf",
    }
    return requests.post(url, headers=h, data=pdf_bytes, timeout=60)


def image_to_pdf(b):
    img = Image.open(io.BytesIO(b))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > 2000:
        img.thumbnail((2000, 2000))
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=200.0)
    return buf.getvalue()


# ----- /self verification -----
try:
    me = api_get("/self", h_tuple())
    agr_no = me.get("agreementNumber", "?")
    st.success(f"✓ **{agreement_name}** · e-conomic #{agr_no}")
except requests.HTTPError as e:
    code = e.response.status_code
    st.error(f"e-conomic afviste ({code}) for **{agreement_name}**. Tjek tokens.")
    st.stop()
except Exception as e:
    st.error(f"Netværksfejl: {e}")
    st.stop()


# ----- 1. Bilag input -----
st.markdown("### 1. Bilag")

tab_cam, tab_file = st.tabs(["📷 Kamera", "📁 Fil"])
image_bytes = None
with tab_cam:
    cam = st.camera_input("Tag billede af bilag", label_visibility="collapsed")
    if cam:
        image_bytes = cam.getvalue()
with tab_file:
    up = st.file_uploader("Vælg billede eller PDF", type=["jpg", "jpeg", "png", "pdf"])
    if up:
        image_bytes = up.getvalue()

if not image_bytes:
    st.info("📸 Tag eller upload et bilag for at starte.")
    st.stop()

is_pdf = image_bytes[:5] == b"%PDF-"


# ----- AI extract -----
@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def extract_with_claude(img_hash, _image_b64, media_type, model, _api_key):
    client = anthropic.Anthropic(api_key=_api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
            }
        ],
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_receipt"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": _image_b64,
                        },
                    },
                    {"type": "text", "text": "Udtræk strukturerede data fra dette bilag."},
                ],
            }
        ],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "extract_receipt":
            return dict(block.input)
    return None


col_img, col_data = st.columns([2, 3])
with col_img:
    if is_pdf:
        st.info("📄 PDF")
    else:
        st.image(image_bytes, use_container_width=True)

extracted = None
if anthropic_key and not is_pdf:
    img_hash = hashlib.md5(image_bytes).hexdigest()
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        media_type = "image/png"
    else:
        media_type = "image/jpeg"
    img_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    with col_data:
        with st.spinner(f"Analyserer med {model_label}..."):
            try:
                extracted = extract_with_claude(
                    img_hash, img_b64, media_type, model_id, anthropic_key
                )
            except Exception as e:
                st.error(f"AI-analyse fejlede: {e}")
elif is_pdf:
    with col_data:
        st.caption("PDF-analyse springes over — vælg postering manuelt.")
elif not anthropic_key:
    with col_data:
        st.caption("Ingen Anthropic-key — manuel valg.")

if extracted:
    with col_data:
        conf = extracted.get("confidence", "low")
        emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "⚪️")
        amt = extracted.get("total_amount") or 0
        st.markdown(f"#### {emoji} Udtrukne data")
        st.markdown(
            f"**Leverandør:** {extracted.get('vendor') or '?'}  \n"
            f"**Dato:** {extracted.get('date') or '—'}  \n"
            f"**Beløb:** {amt:,.2f} {extracted.get('currency') or 'DKK'}  \n"
            f"**Beskrivelse:** {extracted.get('description') or '—'}"
        )


# ----- 2. Hent posteringer + match -----
st.markdown("### 2. Match mod kladde-posteringer")

try:
    journals = api_get("/journals", h_tuple()).get("collection", [])
except Exception as e:
    st.error(f"Kunne ikke hente kladder: {e}")
    st.stop()

if not journals:
    st.warning("Ingen kladder i denne aftale.")
    st.stop()

all_vouchers = []
for j in journals:
    jno = j["journalNumber"]
    try:
        entries = api_get(
            f"/journals/{jno}/entries?pagesize=200", h_tuple()
        ).get("collection", [])
    except Exception:
        continue
    by_voucher = {}
    for e in entries:
        v = e.get("voucherNumber")
        ay = (e.get("accountingYear") or {}).get("year")
        if v is None or ay is None:
            continue
        key = (ay, v)
        if key not in by_voucher:
            by_voucher[key] = {
                "accountingYear": ay,
                "voucherNumber": v,
                "journalNumber": jno,
                "journalName": j["name"],
                "entries": [],
                "date": e.get("date", ""),
                "text": e.get("text", ""),
            }
        by_voucher[key]["entries"].append(e)
    all_vouchers.extend(by_voucher.values())

if not all_vouchers:
    st.warning("Ingen kladde-posteringer fundet i denne aftale.")
    st.stop()


def score_voucher(ex, v):
    if not ex:
        return 0, []
    score = 0
    reasons = []

    v_total = abs(sum(e.get("amount", 0) for e in v["entries"]))
    e_total = abs(ex.get("total_amount") or 0)
    if v_total > 0 and e_total > 0:
        diff_pct = abs(v_total - e_total) / max(v_total, e_total)
        if diff_pct < 0.001:
            score += 60
            reasons.append(f"Beløb matcher præcist ({v_total:,.2f})")
        elif diff_pct < 0.02:
            score += 50
            reasons.append(f"Beløb ~matcher ({v_total:,.2f} vs {e_total:,.2f})")
        elif diff_pct < 0.05:
            score += 30
        elif diff_pct < 0.10:
            score += 10

    try:
        ed = date.fromisoformat(ex["date"])
        vd = date.fromisoformat(v["date"][:10])
        days = abs((ed - vd).days)
        if days == 0:
            score += 25
            reasons.append("Samme dato")
        elif days <= 3:
            score += 18
            reasons.append(f"Dato ±{days} dage")
        elif days <= 7:
            score += 10
        elif days <= 30:
            score += 4
    except Exception:
        pass

    vendor = (ex.get("vendor") or "").lower().strip()
    text = (
        v["text"]
        + " "
        + " ".join(e.get("text", "") for e in v["entries"])
    ).lower()
    if vendor and text:
        if vendor in text or any(p in text for p in vendor.split() if len(p) > 3):
            score += 15
            reasons.append("Leverandør findes i posteringstekst")
        else:
            sim = SequenceMatcher(None, vendor, text).ratio()
            if sim > 0.5:
                score += int(sim * 10)

    return min(score, 100), reasons


if extracted:
    scored = [(score_voucher(extracted, v), v) for v in all_vouchers]
    scored.sort(key=lambda x: x[0][0], reverse=True)
    top = scored[:3]
    top_score = top[0][0][0]

    if top_score >= 70:
        st.success(f"✨ Auto-match · {top_score}% sikker")
    elif top_score >= 40:
        st.info(f"Bedste forslag: {top_score}%. Tjek kandidaterne.")
    else:
        st.warning(
            f"Ingen oplagt match ({top_score}%). Vælg manuelt nedenfor eller "
            "kontrollér at posteringen er oprettet i kladden."
        )

    def fmt_top(i):
        (s, _r), v = top[i]
        total = sum(e.get("amount", 0) for e in v["entries"])
        text = v["text"] or (v["entries"][0].get("text", "") if v["entries"] else "")
        return f"**{s}%** · #{v['voucherNumber']} · {v['date']} · {total:,.2f} kr · {text[:30]}"

    sel = st.radio(
        "Kandidater",
        range(len(top)),
        format_func=fmt_top,
        label_visibility="collapsed",
    )
    selected = top[sel][1]
    sel_reasons = top[sel][0][1]
    if sel_reasons:
        st.caption("→ " + " · ".join(sel_reasons))

    with st.expander("Vis alle posteringer i kladden i stedet"):
        all_sorted = sorted(
            all_vouchers,
            key=lambda v: (v["accountingYear"], v["voucherNumber"]),
            reverse=True,
        )
        labels = [
            f"#{v['voucherNumber']} · {v['date']} · "
            f"{sum(e.get('amount', 0) for e in v['entries']):,.2f} kr · "
            f"{(v['text'] or '')[:30]}"
            for v in all_sorted[:80]
        ]
        manual_idx = st.selectbox(
            "Manuel valg", range(len(labels)), format_func=lambda i: labels[i]
        )
        if st.checkbox("Brug manuelt valg i stedet"):
            selected = all_sorted[manual_idx]
else:
    all_sorted = sorted(
        all_vouchers,
        key=lambda v: (v["accountingYear"], v["voucherNumber"]),
        reverse=True,
    )
    labels = [
        f"#{v['voucherNumber']} · {v['date']} · "
        f"{sum(e.get('amount', 0) for e in v['entries']):,.2f} kr · "
        f"{(v['text'] or '')[:30]}"
        for v in all_sorted[:80]
    ]
    idx = st.radio(
        "Vælg postering",
        range(len(labels)),
        format_func=lambda i: labels[i],
        label_visibility="collapsed",
    )
    selected = all_sorted[idx]


with st.expander("Detaljer for valgt postering"):
    st.write(f"**Kladde:** {selected['journalName']}")
    for e in selected["entries"]:
        acc = (e.get("account") or {}).get("accountNumber", "?")
        contra = (e.get("contraAccount") or {}).get("accountNumber")
        contra_str = f" → {contra}" if contra else ""
        st.write(
            f"- {e.get('text', '')} · {e.get('amount', 0):,.2f} "
            f"{e.get('currency', '')} · konto {acc}{contra_str}"
        )


# ----- 3. Godkend & upload -----
st.markdown("### 3. Godkend & upload")

if st.button(
    f"☁️  Godkend & vedhæft bilag til #{selected['voucherNumber']}",
    type="primary",
):
    with st.spinner("Sender til e-conomic..."):
        try:
            pdf_bytes = image_bytes if is_pdf else image_to_pdf(image_bytes)
            r = upload_attachment(
                selected["journalNumber"],
                selected["accountingYear"],
                selected["voucherNumber"],
                pdf_bytes,
            )
            if r.status_code in (200, 201, 204):
                st.balloons()
                st.success(
                    f"✓ Bilag vedhæftet postering #{selected['voucherNumber']} "
                    f"i **{agreement_name}**"
                )
                api_get.clear()
            else:
                body = r.text[:300] if r.text else f"HTTP {r.status_code}"
                st.error(f"Upload fejlede ({r.status_code}): {body}")
        except Exception as e:
            st.error(f"Fejl: {e}")
