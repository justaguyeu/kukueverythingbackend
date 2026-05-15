"""
KUKU EVERYTHING — Notification Service
=======================================

FREE providers used:
  EMAIL  → Gmail SMTP  (500 emails/day FREE, needs Google App Password)
  SMS    → Africa's Talking SANDBOX (completely free for testing)
           OR Twilio trial ($15 free credits = ~100+ SMS)
           OR console (just prints — zero setup needed for dev)

When no provider is configured, everything goes to the Django console
so you can develop and test without any account at all.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Phone normalizer  (Tanzania numbers)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_tz_phone(phone: str) -> str:
    """
    Convert any TZ phone variant to E.164 (+255XXXXXXXXX).
    Works with:  0712345678  /  255712345678  /  +255712345678
    """
    p = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if p.startswith('0') and len(p) == 10:
        return '+255' + p[1:]
    if p.startswith('255') and not p.startswith('+'):
        return '+' + p
    if not p.startswith('+'):
        return '+255' + p
    return p


# ─────────────────────────────────────────────────────────────────────────────
# SMS Backends
# ─────────────────────────────────────────────────────────────────────────────

def _sms_via_africastalking(phone: str, message: str) -> bool:
    """
    Africa's Talking — FREE sandbox.
    Register at https://africastalking.com/ → use username='sandbox'
    In sandbox the SMS shows in the AT web simulator, NOT a real phone.
    Switch to live by changing username + adding TZS credit (~TZS 25/SMS).
    """
    api_key = settings.AFRICASTALKING_API_KEY
    if not api_key:
        logger.warning("[AT] No API key — SMS skipped. Set AFRICASTALKING_API_KEY in .env")
        return False
    try:
        import africastalking
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=api_key,
        )
        sms = africastalking.SMS
        sender = settings.AFRICASTALKING_SENDER_ID or None
        resp = sms.send(message, [phone], sender_id=sender)
        recipients = resp.get('SMSMessageData', {}).get('Recipients', [])
        for r in recipients:
            if r.get('status') not in ('Success', 'Sent'):
                logger.warning(f"[AT] SMS to {phone} failed: {r}")
                return False
        logger.info(f"[AT] SMS sent → {phone}")
        return True
    except ImportError:
        logger.error("[AT] africastalking package not installed. Run: pip install africastalking")
        return False
    except Exception as e:
        logger.error(f"[AT] Error: {e}")
        return False


def _sms_via_twilio(phone: str, message: str) -> bool:
    """
    Twilio — FREE trial gives $15 credit (~100+ SMS to Tanzania).
    Register at https://twilio.com/ → get Account SID + Auth Token + trial number.
    """
    sid   = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    from_ = settings.TWILIO_FROM_NUMBER
    if not all([sid, token, from_]):
        logger.warning("[Twilio] Credentials missing — SMS skipped.")
        return False
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(body=message, from_=from_, to=phone)
        logger.info(f"[Twilio] SMS sent → {phone} SID={msg.sid}")
        return True
    except ImportError:
        logger.error("[Twilio] Package not installed. Run: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"[Twilio] Error: {e}")
        return False


def _sms_console(phone: str, message: str) -> bool:
    """Development fallback — prints SMS to Django console. Zero setup."""
    border = "═" * 58
    print(f"\n╔{border}╗")
    print(f"║  📱 SMS NOTIFICATION (Console Mode)                    ║")
    print(f"╠{border}╣")
    print(f"║  To : {phone:<50} ║")
    print(f"╠{border}╣")
    for line in message.splitlines():
        while len(line) > 54:
            print(f"║  {line[:54]}  ║")
            line = line[54:]
        print(f"║  {line:<54}  ║")
    print(f"╚{border}╝\n")
    return True


def send_sms(phone: str, message: str) -> bool:
    """
    Send an SMS using the configured provider.
    Provider is set via SMS_PROVIDER in .env:
      'africastalking' (default) | 'twilio' | 'console'
    Falls back to console if provider fails.
    """
    if not phone:
        return False
    phone = normalize_tz_phone(phone)
    provider = getattr(settings, 'SMS_PROVIDER', 'console')

    if provider == 'africastalking':
        ok = _sms_via_africastalking(phone, message)
    elif provider == 'twilio':
        ok = _sms_via_twilio(phone, message)
    else:
        ok = _sms_console(phone, message)

    if not ok:
        # Always fall back to console so nothing is silently lost
        _sms_console(phone, f"[FALLBACK — original provider failed]\n{message}")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, html: str) -> bool:
    """
    Send HTML email.
    In dev (EMAIL_BACKEND = console): prints to terminal — no SMTP needed.
    In prod: set EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
             and fill EMAIL_HOST_USER + EMAIL_HOST_PASSWORD (Gmail App Password).
    """
    if not to:
        return False
    try:
        text = strip_tags(html)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send()
        logger.info(f"[Email] Sent → {to} | {subject}")
        return True
    except Exception as e:
        logger.error(f"[Email] Failed → {to}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Message templates
# ─────────────────────────────────────────────────────────────────────────────

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
    if amount:
        return f"Tsh {int(amount):,}"
    return 'Haijawekwa'


# ── SMS templates ─────────────────────────────────────────

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
        f"Ingia dashboard: kukueverything.co.tz/dashboard"
    )


def sms_customer_status(order) -> str:
    status_sw = STATUS_SW.get(order.status, order.status)
    emoji     = STATUS_EMOJI.get(order.status, '📦')
    extra = {
        'confirmed':  f"Muuzaji amethibitisha! Atawasiliana nawe.\nSimu: {order.business.phone}",
        'processing': f"Order yako inaandaliwa. Muuzaji: {order.business.phone}",
        'completed':  f"Asante! Acha review: kukueverything.co.tz/businesses/{order.business.pk}",
        'cancelled':  f"Order imefutwa. Wasiliana: {order.business.phone}",
    }.get(order.status, '')
    return (
        f"{emoji} KUKU EVERYTHING\n"
        f"Order #{order.pk}: {status_sw.upper()}\n"
        f"Bidhaa: {order.product_name} x{order.quantity}\n"
        f"Biashara: {order.business.name}\n"
        + (extra + "\n" if extra else "")
    )


# ── Email HTML templates ──────────────────────────────────

def _email_wrapper(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="sw">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&family=Montserrat:wght@400;500;600;700&display=swap');
    body{{margin:0;padding:0;background:#f5f5f5;font-family:Montserrat,Arial,sans-serif;}}
    .wrap{{max-width:620px;margin:24px auto;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e0e0e0;box-shadow:0 4px 20px rgba(0,0,0,.08);}}
    .header{{background:linear-gradient(135deg,#1B5E20,#2E7D32);padding:28px 36px;text-align:center;}}
    .logo{{font-family:Oswald,Georgia,serif;font-size:28px;font-weight:700;color:#fff;letter-spacing:2px;}}
    .logo span{{color:#F9A825;}}
    .tagline{{color:rgba(255,255,255,.75);font-size:13px;margin-top:4px;}}
    .body{{padding:32px 36px;}}
    .alert{{border-left:4px solid;padding:14px 18px;border-radius:0 8px 8px 0;margin-bottom:24px;}}
    .alert-title{{font-size:18px;font-weight:700;font-family:Oswald,serif;letter-spacing:.5px;}}
    .alert-sub{{font-size:13px;color:#555;margin-top:4px;}}
    .section-title{{font-family:Oswald,serif;font-size:14px;font-weight:700;color:#1B5E20;letter-spacing:1px;text-transform:uppercase;margin:0 0 10px;}}
    table.info{{width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;margin-bottom:20px;font-size:13px;}}
    table.info tr:nth-child(odd){{background:#f9f9f9;}}
    table.info td{{padding:9px 14px;vertical-align:top;}}
    table.info td:first-child{{font-weight:600;color:#444;width:38%;}}
    table.info td:last-child{{color:#222;}}
    .btn{{display:inline-block;background:#1B5E20;color:#fff!important;padding:13px 32px;border-radius:30px;font-weight:700;font-size:14px;text-decoration:none;font-family:Oswald,serif;letter-spacing:.5px;}}
    .btn-wa{{background:#25D366;}}
    .btn-center{{text-align:center;margin:24px 0 8px;}}
    .review-box{{background:#FFF8E1;border:1px solid #F9A825;border-radius:8px;padding:16px 20px;margin-top:16px;text-align:center;}}
    .footer{{background:#f0f0f0;padding:16px 36px;text-align:center;font-size:12px;color:#999;}}
    a{{color:#1B5E20;}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="logo">KUKU <span>EVERYTHING</span> 🐓</div>
      <div class="tagline">Tanzania's #1 Chicken Marketplace</div>
    </div>
    <div class="body">{content}</div>
    <div class="footer">
      © 2025 KUKU EVERYTHING · Tanzania 🇹🇿 ·
      <a href="http://kukueverything.co.tz">kukueverything.co.tz</a>
    </div>
  </div>
</body>
</html>"""


def email_owner_new_order_html(order) -> str:
    price_row   = f"<tr><td>Jumla ya Bei</td><td><strong style='color:#1B5E20'>{_fmt_price(order.total_amount)}</strong></td></tr>" if order.total_amount else ""
    notes_row   = f"<tr><td>Maelezo</td><td>{order.notes}</td></tr>" if order.notes else ""
    email_row   = f"<tr><td>Email</td><td>{order.customer_email}</td></tr>" if order.customer_email else ""
    region_row  = f"<tr><td>Mkoa wa Mteja</td><td>{order.customer_region}</td></tr>" if order.customer_region else ""
    address_row = f"<tr><td>Anwani ya Delivery</td><td>{order.delivery_address}</td></tr>" if order.delivery_address else ""

    content = f"""
    <div class="alert" style="background:#E8F5E9;border-color:#4CAF50;">
      <div class="alert-title" style="color:#1B5E20;">🎉 Agizo Jipya — Order #{order.pk}</div>
      <div class="alert-sub">Imepokelewa saa hivi. Ingia dashboard kuthibitisha.</div>
    </div>

    <p class="section-title">TAARIFA ZA MTEJA</p>
    <table class="info">
      <tr><td>Jina Kamili</td><td><strong>{order.customer_name}</strong></td></tr>
      <tr><td>Simu</td><td><a href="tel:{order.customer_phone}"><strong>{order.customer_phone}</strong></a></td></tr>
      {email_row}
      {region_row}
      {address_row}
    </table>

    <p class="section-title">MAELEZO YA BIDHAA</p>
    <table class="info">
      <tr><td>Bidhaa</td><td><strong>{order.product_name}</strong></td></tr>
      <tr><td>Idadi (Quantity)</td><td><strong>{order.quantity}</strong></td></tr>
      {price_row}
      <tr><td>Njia ya Kuwasiliana</td><td>{order.get_contact_method_display()}</td></tr>
      {notes_row}
    </table>

    <div class="btn-center">
      <a class="btn" href="http://kukueverything.co.tz/dashboard">📊 FUNGUA DASHBOARD</a>
    </div>
    <p style="text-align:center;font-size:13px;color:#888;margin-top:8px;">
      Wasiliana na mteja:
      <a href="https://wa.me/{order.customer_phone}" style="color:#25D366;font-weight:700;">💬 WhatsApp</a>
      &nbsp;|&nbsp;
      <a href="tel:{order.customer_phone}" style="color:#1B5E20;font-weight:700;">📞 Piga Simu</a>
    </p>"""
    return _email_wrapper(content)


def email_customer_status_html(order) -> str:
    status_sw    = STATUS_SW.get(order.status, order.status)
    emoji        = STATUS_EMOJI.get(order.status, '📦')
    color        = STATUS_COLOR.get(order.status, '#333')
    bg           = STATUS_BG.get(order.status, '#f5f5f5')
    price_row    = f"<tr><td>Jumla ya Bei</td><td><strong style='color:#1B5E20'>{_fmt_price(order.total_amount)}</strong></td></tr>" if order.total_amount else ""
    address_row  = f"<tr><td>Anwani</td><td>{order.delivery_address}</td></tr>" if order.delivery_address else ""

    review_block = ""
    if order.status == 'completed':
        review_block = f"""
        <div class="review-box">
          <div style="font-weight:700;color:#F57C00;margin-bottom:8px;font-family:Oswald,serif;font-size:16px;letter-spacing:.5px;">
            ⭐ ULIFURAHIA HUDUMA?
          </div>
          <p style="font-size:13px;color:#555;margin:0 0 12px;">Wasaidie wengine kwa kuacha review yako</p>
          <a href="http://kukueverything.co.tz/businesses/{order.business.pk}"
             style="background:#F9A825;color:#1B5E20;padding:10px 24px;border-radius:20px;text-decoration:none;font-weight:700;font-size:14px;font-family:Oswald,serif;">
            ANDIKA REVIEW
          </a>
        </div>"""

    content = f"""
    <div class="alert" style="background:{bg};border-color:{color};">
      <div class="alert-title" style="color:{color};">{emoji} Order #{order.pk} — {status_sw.upper()}</div>
      <div class="alert-sub">Hali ya order yako imebadilika. Maelezo hapa chini.</div>
    </div>

    <p class="section-title">MAELEZO YA ORDER YAKO</p>
    <table class="info">
      <tr><td>Bidhaa</td><td><strong>{order.product_name}</strong></td></tr>
      <tr><td>Idadi</td><td>{order.quantity}</td></tr>
      {price_row}
      <tr><td>Hali Mpya</td>
          <td><strong style="color:{color};background:{bg};padding:3px 10px;border-radius:12px;font-size:12px;">
            {emoji} {status_sw.upper()}
          </strong></td></tr>
      {address_row}
    </table>

    <p class="section-title">TAARIFA ZA MUUZAJI</p>
    <table class="info">
      <tr><td>Biashara</td><td><strong>{order.business.name}</strong></td></tr>
      <tr><td>Mkoa</td><td>{order.business.region}</td></tr>
      <tr><td>Simu</td><td><a href="tel:{order.business.phone}"><strong>{order.business.phone}</strong></a></td></tr>
    </table>

    {review_block}"""
    return _email_wrapper(content)


# ─────────────────────────────────────────────────────────────────────────────
# Public notification functions  (called from orders/views.py)
# ─────────────────────────────────────────────────────────────────────────────

def notify_owner_new_order(order) -> None:
    """
    Called immediately after a new order is created.
    → SMS  to business phone (always)
    → SMS  to owner personal phone (if different)
    → Email to owner email
    """
    try:
        owner        = order.business.owner
        biz_phone    = order.business.phone
        owner_phone  = owner.phone or ''
        owner_email  = owner.email or ''

        # SMS to business phone
        send_sms(biz_phone, sms_owner_new_order(order))

        # SMS to owner personal phone if it differs
        if owner_phone and normalize_tz_phone(owner_phone) != normalize_tz_phone(biz_phone):
            send_sms(owner_phone, sms_owner_new_order(order))

        # Email
        if owner_email:
            send_email(
                to=owner_email,
                subject=f"🐓 Agizo Jipya #{order.pk} kutoka {order.customer_name} | KUKU EVERYTHING",
                html=email_owner_new_order_html(order),
            )

        logger.info(f"[Notify] Owner notified → order #{order.pk}")
    except Exception as exc:
        logger.error(f"[Notify] owner_new_order failed for #{order.pk}: {exc}")


def notify_customer_status_update(order) -> None:
    """
    Called whenever a business owner updates the order status.
    Fires for: processing, confirmed, completed, cancelled.
    → SMS  to customer phone
    → Email to customer email (if provided)
    """
    if order.status == 'pending':
        return  # no notification on initial state

    try:
        c_phone = order.customer_phone or ''
        c_email = order.customer_email or ''

        if c_phone:
            send_sms(c_phone, sms_customer_status(order))

        if c_email:
            status_sw = STATUS_SW.get(order.status, order.status)
            send_email(
                to=c_email,
                subject=f"📦 Order #{order.pk} — {status_sw.upper()} | KUKU EVERYTHING",
                html=email_customer_status_html(order),
            )

        logger.info(f"[Notify] Customer notified → order #{order.pk} status={order.status}")
    except Exception as exc:
        logger.error(f"[Notify] customer_status_update failed for #{order.pk}: {exc}")
