"""
KUKU EVERYTHING — Notification Service
=======================================

SMS PROVIDERS (choose in .env):
  'beem'          → Beem Africa  — BEST for Tanzania (~TZS 18/SMS, widely used)
                    Register free: https://beem.africa/
  'africastalking'→ Africa's Talking (~TZS 25/SMS, free sandbox)
                    Register free: https://africastalking.com/
  'console'       → Prints to terminal. Zero setup. Use in development.

EMAIL:
  Gmail SMTP free (500/day). Set EMAIL_BACKEND=smtp in .env.
  In dev, leave as 'console' — emails print to terminal.

EMAIL HTML FIX:
  Django console backend prints the raw MIME message. The HTML you see
  in console is the actual email content — it is correct. When SMTP is
  configured, the customer's email client will render it beautifully.
"""

import logging
import requests as http_requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ── Phone normaliser ────────────────────────────────────────────────────────

def normalize_tz_phone(phone: str) -> str:
    """Normalise any TZ phone to E.164 (+255XXXXXXXXX)."""
    p = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if p.startswith('0') and len(p) == 10:
        return '+255' + p[1:]
    if p.startswith('255') and not p.startswith('+'):
        return '+' + p
    if not p.startswith('+'):
        return '+255' + p
    return p


# ── SMS backends ────────────────────────────────────────────────────────────

def _sms_beem(phone: str, message: str) -> bool:
    """
    Beem Africa — Tanzania's most popular SMS gateway.
    ~TZS 18 per SMS. Much cheaper than AT or Twilio for TZ numbers.

    Setup (5 minutes, free registration):
      1. Go to https://beem.africa/ and sign up
      2. Dashboard → API Access → copy API Key & Secret Key
      3. Add balance (minimum TZS 5,000 to start)
      4. Set SMS_PROVIDER=beem in .env
         BEEM_API_KEY=your_api_key
         BEEM_SECRET_KEY=your_secret_key
         BEEM_SENDER_NAME=KUKU  (up to 11 chars — register with Beem first)
    """
    api_key    = getattr(settings, 'BEEM_API_KEY', '')
    secret_key = getattr(settings, 'BEEM_SECRET_KEY', '')
    sender     = getattr(settings, 'BEEM_SENDER_NAME', 'KUKU')

    if not api_key or not secret_key:
        logger.warning("[Beem] No credentials — SMS skipped. Set BEEM_API_KEY and BEEM_SECRET_KEY in .env")
        return False

    # Strip leading '+' for Beem — it expects numbers without '+'
    dest = phone.lstrip('+')

    payload = {
        "source_addr": sender,
        "encoding":    0,
        "message":     message,
        "recipients":  [{"recipient_id": 1, "dest_addr": dest}],
    }
    try:
        resp = http_requests.post(
            "https://apisms.beem.africa/v1/send",
            json=payload,
            auth=(api_key, secret_key),
            timeout=15,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("successful"):
            logger.info(f"[Beem] SMS sent → {phone}")
            return True
        else:
            logger.warning(f"[Beem] SMS failed → {phone}: {data}")
            return False
    except Exception as exc:
        logger.error(f"[Beem] Error: {exc}")
        return False


def _sms_africastalking(phone: str, message: str) -> bool:
    """
    Africa's Talking — free sandbox for testing.
    sandbox: SMS shows in AT web simulator (not real phone).
    live:    ~TZS 25/SMS.
    """
    api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
    if not api_key:
        logger.warning("[AT] No API key — SMS skipped.")
        return False
    try:
        import africastalking
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=api_key,
        )
        sms    = africastalking.SMS
        sender = settings.AFRICASTALKING_SENDER_ID or None
        resp   = sms.send(message, [phone], sender_id=sender)
        for r in resp.get('SMSMessageData', {}).get('Recipients', []):
            if r.get('status') not in ('Success', 'Sent'):
                logger.warning(f"[AT] SMS to {phone} failed: {r}")
                return False
        logger.info(f"[AT] SMS sent → {phone}")
        return True
    except ImportError:
        logger.error("[AT] africastalking not installed. Run: pip install africastalking")
        return False
    except Exception as exc:
        logger.error(f"[AT] Error: {exc}")
        return False


def _sms_console(phone: str, message: str) -> bool:
    """Development fallback — prints SMS to Django console."""
    border = "═" * 60
    print(f"\n╔{border}╗")
    print(f"║  📱 SMS  →  {phone:<46} ║")
    print(f"╠{border}╣")
    for line in message.splitlines():
        while len(line) > 56:
            print(f"║  {line[:56]}  ║")
            line = line[56:]
        print(f"║  {line:<56}  ║")
    print(f"╚{border}╝\n")
    return True


def send_sms(phone: str, message: str) -> bool:
    if not phone:
        return False
    phone    = normalize_tz_phone(phone)
    provider = getattr(settings, 'SMS_PROVIDER', 'console')

    if provider == 'beem':
        ok = _sms_beem(phone, message)
    elif provider == 'africastalking':
        ok = _sms_africastalking(phone, message)
    else:
        ok = _sms_console(phone, message)

    if not ok:
        _sms_console(phone, f"[FALLBACK — {provider} failed]\n{message}")
    return ok


# ── Email ────────────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, html: str) -> bool:
    """
    Send HTML email.

    HOW TO CONFIGURE GMAIL SMTP (free, 5 min):
      1. myaccount.google.com → Security → 2-Step Verification ON
      2. Search "App passwords" → Mail → generate 16-char password
      3. In .env:
           EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
           EMAIL_HOST=smtp.gmail.com
           EMAIL_PORT=587
           EMAIL_USE_TLS=True
           EMAIL_HOST_USER=yourgmail@gmail.com
           EMAIL_HOST_PASSWORD=abcdefghijklmnop
           DEFAULT_FROM_EMAIL=KUKU EVERYTHING <yourgmail@gmail.com>

    WHY YOU SEE RAW HTML IN CONSOLE:
      The console email backend prints the full MIME message source —
      the HTML inside is correct and will render properly in a real
      email client once SMTP is configured.
    """
    if not to:
        return False
    try:
        text = strip_tags(html)
        msg  = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send()
        logger.info(f"[Email] Sent → {to} | {subject}")
        return True
    except Exception as exc:
        logger.error(f"[Email] Failed → {to}: {exc}")
        return False


# ── Message templates ────────────────────────────────────────────────────────

STATUS_SW = {
    'pending':    'Inasubiri',
    'processing': 'Inaandaliwa',
    'confirmed':  'Imethibitishwa',
    'completed':  'Imekamilika',
    'cancelled':  'Imefutwa',
}
STATUS_EMOJI = {
    'pending':    '⏳',
    'processing': '⚙️',
    'confirmed':  '✅',
    'completed':  '🎉',
    'cancelled':  '❌',
}
STATUS_COLOR = {
    'pending':    '#F57C00',
    'processing': '#1565C0',
    'confirmed':  '#2E7D32',
    'completed':  '#2E7D32',
    'cancelled':  '#C62828',
}
STATUS_BG = {
    'pending':    '#FFF3E0',
    'processing': '#E3F2FD',
    'confirmed':  '#E8F5E9',
    'completed':  '#E8F5E9',
    'cancelled':  '#FFEBEE',
}


def _fmt_price(amount) -> str:
    return f"Tsh {int(amount):,}" if amount else 'Haijawekwa'


# SMS text ────────────────────────────────────────────────────────────────────

def sms_owner_new_order(order) -> str:
    price = f" | Jumla: {_fmt_price(order.total_amount)}" if order.total_amount else ""
    notes = f"\nMaelezo: {order.notes}" if order.notes else ""
    return (
        f"KUKU EVERYTHING - AGIZO JIPYA!\n"
        f"Order #{order.pk}\n"
        f"Mteja: {order.customer_name}\n"
        f"Simu: {order.customer_phone}\n"
        f"Bidhaa: {order.product_name} x{order.quantity}{price}\n"
        f"Anwani: {order.delivery_address or 'Haijatajwa'}\n"
        f"Mkoa: {order.customer_region or 'Haijatajwa'}"
        f"{notes}\n"
        f"Dashboard: kukueverything.co.tz/dashboard"
    )


def sms_customer_status(order) -> str:
    sw    = STATUS_SW.get(order.status, order.status)
    emoji = STATUS_EMOJI.get(order.status, '📦')
    extra = {
        'confirmed':  f"Muuzaji amethibitisha! Atawasiliana nawe.\nSimu: {order.business.phone}",
        'processing': f"Order yako inaandaliwa. Muuzaji: {order.business.phone}",
        'completed':  f"Asante! Acha review: kukueverything.co.tz/businesses/{order.business.pk}",
        'cancelled':  f"Order imefutwa. Wasiliana: {order.business.phone}",
    }.get(order.status, '')
    return (
        f"{emoji} KUKU EVERYTHING\n"
        f"Order #{order.pk}: {sw.upper()}\n"
        f"Bidhaa: {order.product_name} x{order.quantity}\n"
        f"Biashara: {order.business.name}\n"
        + (extra + "\n" if extra else "")
    )


# Email HTML ──────────────────────────────────────────────────────────────────

def _wrap(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="sw">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
body{{margin:0;padding:16px;background:#f0f0f0;font-family:Arial,sans-serif;font-size:14px;color:#222;}}
.wrap{{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #ddd;}}
.hdr{{background:linear-gradient(135deg,#1B5E20,#2E7D32);padding:24px 28px;text-align:center;}}
.logo{{font-size:24px;font-weight:700;color:#fff;letter-spacing:2px;}}
.logo span{{color:#F9A825;}}
.tag{{color:rgba(255,255,255,.7);font-size:12px;margin-top:4px;}}
.bod{{padding:24px 28px;}}
.alert{{border-left:4px solid;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:20px;}}
.alert-title{{font-size:17px;font-weight:700;}}
.alert-sub{{font-size:13px;color:#555;margin-top:3px;}}
.sec{{font-size:11px;font-weight:700;color:#1B5E20;letter-spacing:1px;text-transform:uppercase;margin:0 0 8px;}}
table{{width:100%;border-collapse:collapse;margin-bottom:18px;font-size:13px;border-radius:8px;overflow:hidden;}}
tr:nth-child(odd){{background:#f8f8f8;}}
td{{padding:8px 12px;vertical-align:top;}}
td:first-child{{font-weight:600;color:#444;width:38%;}}
.btn{{display:inline-block;background:#1B5E20;color:#fff;padding:12px 28px;border-radius:24px;font-weight:700;font-size:14px;text-decoration:none;margin:8px 4px;}}
.btn-wa{{background:#25D366;}}
.ctr{{text-align:center;margin:20px 0 8px;}}
.review-box{{background:#FFF8E1;border:1px solid #F9A825;border-radius:8px;padding:14px 18px;margin-top:14px;text-align:center;}}
.ftr{{background:#f0f0f0;padding:14px 28px;text-align:center;font-size:11px;color:#999;}}
a{{color:#1B5E20;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="logo">KUKU <span>EVERYTHING</span> 🐓</div>
    <div class="tag">Tanzania's #1 Chicken Marketplace</div>
  </div>
  <div class="bod">{body}</div>
  <div class="ftr">© 2025 KUKU EVERYTHING · Tanzania 🇹🇿 · <a href="http://kukueverything.co.tz">kukueverything.co.tz</a></div>
</div>
</body>
</html>"""


def email_owner_new_order_html(order) -> str:
    price_row   = f"<tr><td>Jumla ya Bei</td><td><strong style='color:#1B5E20'>{_fmt_price(order.total_amount)}</strong></td></tr>" if order.total_amount else ""
    notes_row   = f"<tr><td>Maelezo</td><td>{order.notes}</td></tr>" if order.notes else ""
    email_row   = f"<tr><td>Email</td><td>{order.customer_email}</td></tr>" if order.customer_email else ""
    region_row  = f"<tr><td>Mkoa wa Mteja</td><td>{order.customer_region}</td></tr>" if order.customer_region else ""
    address_row = f"<tr><td>Anwani ya Delivery</td><td>{order.delivery_address}</td></tr>" if order.delivery_address else ""

    body = f"""
<div class="alert" style="background:#E8F5E9;border-color:#4CAF50;">
  <div class="alert-title" style="color:#1B5E20;">🎉 Agizo Jipya — Order #{order.pk}</div>
  <div class="alert-sub">Imepokelewa saa hivi. Ingia dashboard kuthibitisha.</div>
</div>
<p class="sec">TAARIFA ZA MTEJA</p>
<table>
  <tr><td>Jina Kamili</td><td><strong>{order.customer_name}</strong></td></tr>
  <tr><td>Simu</td><td><a href="tel:{order.customer_phone}"><strong>{order.customer_phone}</strong></a></td></tr>
  {email_row}{region_row}{address_row}
</table>
<p class="sec">MAELEZO YA BIDHAA</p>
<table>
  <tr><td>Bidhaa</td><td><strong>{order.product_name}</strong></td></tr>
  <tr><td>Idadi</td><td><strong>{order.quantity}</strong></td></tr>
  {price_row}
  <tr><td>Njia</td><td>{order.get_contact_method_display()}</td></tr>
  {notes_row}
</table>
<div class="ctr">
  <a class="btn" href="http://kukueverything.co.tz/dashboard">📊 FUNGUA DASHBOARD</a>
  <a class="btn btn-wa" href="https://wa.me/{order.customer_phone}">💬 WhatsApp Mteja</a>
</div>"""
    return _wrap(body)


def email_customer_status_html(order) -> str:
    sw      = STATUS_SW.get(order.status, order.status)
    emoji   = STATUS_EMOJI.get(order.status, '📦')
    color   = STATUS_COLOR.get(order.status, '#333')
    bg      = STATUS_BG.get(order.status, '#f5f5f5')
    price_row   = f"<tr><td>Jumla ya Bei</td><td><strong style='color:#1B5E20'>{_fmt_price(order.total_amount)}</strong></td></tr>" if order.total_amount else ""
    address_row = f"<tr><td>Anwani</td><td>{order.delivery_address}</td></tr>" if order.delivery_address else ""

    review_block = ""
    if order.status == 'completed':
        review_block = f"""
<div class="review-box">
  <div style="font-weight:700;color:#F57C00;margin-bottom:6px;font-size:15px;">⭐ ULIFURAHIA HUDUMA?</div>
  <p style="font-size:13px;color:#555;margin:0 0 10px;">Wasaidie wengine kwa kuacha review yako</p>
  <a href="http://kukueverything.co.tz/businesses/{order.business.pk}" class="btn" style="background:#F9A825;color:#1B5E20;">ANDIKA REVIEW</a>
</div>"""

    body = f"""
<div class="alert" style="background:{bg};border-color:{color};">
  <div class="alert-title" style="color:{color};">{emoji} Order #{order.pk} — {sw.upper()}</div>
  <div class="alert-sub">Hali ya order yako imebadilika. Maelezo hapa chini.</div>
</div>
<p class="sec">MAELEZO YA ORDER YAKO</p>
<table>
  <tr><td>Bidhaa</td><td><strong>{order.product_name}</strong></td></tr>
  <tr><td>Idadi</td><td>{order.quantity}</td></tr>
  {price_row}
  <tr><td>Hali Mpya</td><td><strong style="color:{color};background:{bg};padding:3px 8px;border-radius:10px;font-size:12px;">{emoji} {sw.upper()}</strong></td></tr>
  {address_row}
</table>
<p class="sec">TAARIFA ZA MUUZAJI</p>
<table>
  <tr><td>Biashara</td><td><strong>{order.business.name}</strong></td></tr>
  <tr><td>Mkoa</td><td>{order.business.region}</td></tr>
  <tr><td>Simu</td><td><a href="tel:{order.business.phone}"><strong>{order.business.phone}</strong></a></td></tr>
</table>
{review_block}"""
    return _wrap(body)


# ── Public functions ─────────────────────────────────────────────────────────

def notify_owner_new_order(order) -> None:
    try:
        owner      = order.business.owner
        biz_phone  = order.business.phone
        own_phone  = owner.phone or ''
        own_email  = owner.email or ''

        send_sms(biz_phone, sms_owner_new_order(order))
        if own_phone and normalize_tz_phone(own_phone) != normalize_tz_phone(biz_phone):
            send_sms(own_phone, sms_owner_new_order(order))
        if own_email:
            send_email(
                to=own_email,
                subject=f"🐓 Agizo Jipya #{order.pk} kutoka {order.customer_name} | KUKU EVERYTHING",
                html=email_owner_new_order_html(order),
            )
        logger.info(f"[Notify] Owner notified → order #{order.pk}")
    except Exception as exc:
        logger.error(f"[Notify] owner_new_order failed #{order.pk}: {exc}")


def notify_customer_status_update(order) -> None:
    if order.status == 'pending':
        return
    try:
        c_phone = order.customer_phone or ''
        c_email = order.customer_email or ''
        if c_phone:
            send_sms(c_phone, sms_customer_status(order))
        if c_email:
            sw = STATUS_SW.get(order.status, order.status)
            send_email(
                to=c_email,
                subject=f"📦 Order #{order.pk} — {sw.upper()} | KUKU EVERYTHING",
                html=email_customer_status_html(order),
            )
        logger.info(f"[Notify] Customer notified → order #{order.pk} status={order.status}")
    except Exception as exc:
        logger.error(f"[Notify] customer_status_update failed #{order.pk}: {exc}")
