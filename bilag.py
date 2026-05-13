import streamlit as st
import requests
from PIL import Image
import io

st.set_page_config(
    page_title="E-conomic Bilag",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container { padding-top: 1.2rem; padding-bottom: 4rem; max-width: 720px; }
        h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, "SF Pro", sans-serif; color: #1d1d1f; font-weight: 600; }
        h1 { text-align: center; font-size: 1.7rem; margin-bottom: 0.2rem; }
        h3 { font-size: 0.95rem; color: #86868b; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 1.4rem; }
        .stButton>button {
            border-radius: 12px; background-color: #0071e3; color: white;
            border: none; font-weight: 500; padding: 10px 20px; width: 100%;
        }
        .stButton>button:hover { background-color: #0077ed; color: white; }
        div[data-testid="stExpander"] { background-color: white; border-radius: 12px; border: 1px solid #e5e5ea; }
        div[data-testid="stRadio"] > div { background-color: white; padding: 8px 14px; border-radius: 12px; border: 1px solid #e5e5ea; }
        div[data-testid="stSelectbox"] > div > div { background-color: white; border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; background: #f5f5f7; }
        .stTabs [aria-selected="true"] { background: #0071e3 !important; color: white !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Bilag → e-conomic")
st.caption("Tag billede af en kvittering og vedhæft den til en kladde-postering")

BASE_URL = "https://restapi.e-conomic.com"


def _secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return None


with st.sidebar:
    st.subheader("API-Forbindelse")
    app_secret = _secret("ECONOMIC_APP_SECRET") or st.text_input(
        "App Secret Token", type="password", key="_app_secret"
    )
    grant_token = _secret("ECONOMIC_GRANT_TOKEN") or st.text_input(
        "Agreement Grant Token", type="password", key="_grant_token"
    )
    st.markdown(
        "Find dine tokens i e-conomic udvikler-portalen. "
        "App Secret Token udstedes til din app; Agreement Grant Token "
        "udstedes når aftalen tilslutter appen."
    )

if not app_secret or not grant_token:
    st.info("Indtast dine e-conomic API-tokens i sidebar (☰ øverst til venstre).")
    st.stop()

HEADERS = {
    "X-AppSecretToken": app_secret,
    "X-AgreementGrantToken": grant_token,
    "Content-Type": "application/json",
}


@st.cache_data(ttl=60, show_spinner=False)
def api_get(endpoint, headers_tuple):
    headers = dict(headers_tuple)
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def headers_tuple():
    return tuple(sorted(HEADERS.items()))


def upload_attachment(journal_no, accounting_year, voucher_no, pdf_bytes):
    url = (
        f"{BASE_URL}/journals/{journal_no}/vouchers/"
        f"{accounting_year}-{voucher_no}/attachment/file"
    )
    h = {
        "X-AppSecretToken": app_secret,
        "X-AgreementGrantToken": grant_token,
        "Content-Type": "application/pdf",
    }
    return requests.post(url, headers=h, data=pdf_bytes, timeout=60)


def image_to_pdf(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > 2000:
        img.thumbnail((2000, 2000))
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=200.0)
    return buf.getvalue()


# --- Forbindelses-tjek ---
try:
    me = api_get("/self", headers_tuple())
    st.success(f"✓ Forbundet til aftale {me.get('agreementNumber', '?')}")
except requests.HTTPError as e:
    code = e.response.status_code
    if code in (401, 403):
        st.error(f"Forbindelse afvist ({code}). Tjek dine tokens.")
    else:
        st.error(f"e-conomic returnerede {code}: {e.response.text[:200]}")
    st.stop()
except Exception as e:
    st.error(f"Netværksfejl: {e}")
    st.stop()


# --- Kladder ---
try:
    journals = api_get("/journals", headers_tuple()).get("collection", [])
except Exception as e:
    st.error(f"Kunne ikke hente kladder: {e}")
    st.stop()

if not journals:
    st.warning("Ingen kladder fundet. Opret en kladde i e-conomic først.")
    st.stop()

st.markdown("### 1. Kladde")
journal_options = {f"{j['name']} · #{j['journalNumber']}": j for j in journals}
journal_label = st.selectbox(
    "Kladde", list(journal_options.keys()), label_visibility="collapsed"
)
journal = journal_options[journal_label]
journal_no = journal["journalNumber"]


# --- Posteringer i valgt kladde ---
try:
    entries = api_get(
        f"/journals/{journal_no}/entries?pagesize=100", headers_tuple()
    ).get("collection", [])
except Exception as e:
    st.error(f"Kunne ikke hente posteringer: {e}")
    st.stop()

vouchers = {}
for entry in entries:
    v = entry.get("voucherNumber")
    ay = (entry.get("accountingYear") or {}).get("year")
    if v is None or ay is None:
        continue
    key = (ay, v)
    if key not in vouchers:
        vouchers[key] = {
            "accountingYear": ay,
            "voucherNumber": v,
            "entries": [],
            "date": entry.get("date", ""),
            "text": entry.get("text", ""),
        }
    vouchers[key]["entries"].append(entry)

st.markdown(f"### 2. Postering ({len(vouchers)} bilag i kladden)")

if not vouchers:
    st.info("Ingen posteringer i denne kladde endnu. Opret en i e-conomic.")
    st.stop()

voucher_list = sorted(
    vouchers.values(),
    key=lambda v: (v["accountingYear"], v["voucherNumber"]),
    reverse=True,
)


def fmt(v):
    total = sum(e.get("amount", 0) for e in v["entries"])
    text = v["text"] or (v["entries"][0].get("text", "") if v["entries"] else "")
    return f"#{v['voucherNumber']} · {v['date']} · {total:,.2f} kr · {text[:32]}"


labels = [fmt(v) for v in voucher_list]
idx = st.radio(
    "Vælg postering",
    range(len(voucher_list)),
    format_func=lambda i: labels[i],
    label_visibility="collapsed",
)
selected = voucher_list[idx]

with st.expander("Vis posteringslinjer"):
    for e in selected["entries"]:
        acc = (e.get("account") or {}).get("accountNumber", "?")
        contra = (e.get("contraAccount") or {}).get("accountNumber")
        contra_str = f" → konto {contra}" if contra else ""
        st.write(
            f"- **{e.get('text', '')}** · {e.get('amount', 0):,.2f} "
            f"{e.get('currency', '')} · konto {acc}{contra_str}"
        )


# --- Bilag ---
st.markdown("### 3. Bilag")
tab_cam, tab_file = st.tabs(["📷 Kamera", "📁 Fil"])

image_bytes = None
with tab_cam:
    cam = st.camera_input("Tag billede af kvittering", label_visibility="collapsed")
    if cam:
        image_bytes = cam.getvalue()

with tab_file:
    uploaded = st.file_uploader(
        "Vælg billede eller PDF", type=["jpg", "jpeg", "png", "pdf"]
    )
    if uploaded:
        image_bytes = uploaded.getvalue()

if image_bytes:
    is_pdf = image_bytes[:5] == b"%PDF-"
    if is_pdf:
        st.success("📄 PDF klar — klar til upload")
    else:
        st.image(image_bytes, use_container_width=True)

    if st.button(
        f"☁️  Upload til postering #{selected['voucherNumber']}",
        type="primary",
    ):
        with st.spinner("Sender bilag til e-conomic..."):
            try:
                pdf_bytes = image_bytes if is_pdf else image_to_pdf(image_bytes)
                resp = upload_attachment(
                    journal_no,
                    selected["accountingYear"],
                    selected["voucherNumber"],
                    pdf_bytes,
                )
                if resp.status_code in (200, 201, 204):
                    st.balloons()
                    st.success(
                        f"✓ Bilag vedhæftet postering #{selected['voucherNumber']}"
                    )
                    api_get.clear()
                else:
                    body = resp.text[:300] if resp.text else f"HTTP {resp.status_code}"
                    st.error(f"Upload fejlede ({resp.status_code}): {body}")
            except Exception as e:
                st.error(f"Fejl under upload: {e}")
