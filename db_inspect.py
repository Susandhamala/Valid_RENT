from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.certificate import Certificate
from app.models.asset import AssetCategory, RentalAsset
from app.models.agreement import RentalAgreement
from app.models.request import AgreementRequest
from app.models.chat import ChatThread, ChatMessage
from app.models.photo import IdentityPhoto
from app.models.pdf import GeneratedPDF

app = create_app()
with app.app_context():
    print("=== TABLE ROW COUNTS ===")
    print("users              :", User.query.count())
    print("certificates       :", Certificate.query.count())
    print("asset_categories   :", AssetCategory.query.count())
    print("rental_assets      :", RentalAsset.query.count())
    print("rental_agreements  :", RentalAgreement.query.count())
    print("agreement_requests :", AgreementRequest.query.count())
    print("chat_threads       :", ChatThread.query.count())
    print("chat_messages      :", ChatMessage.query.count())
    print("identity_photos    :", IdentityPhoto.query.count())
    print("generated_pdfs     :", GeneratedPDF.query.count())

    print("\n=== USERS ===")
    for u in User.query.all():
        cert = Certificate.query.filter_by(user_id=u.id).first()
        serial = cert.serial_number[:20] + "..." if cert else "none"
        print(f"  [{u.id}] {u.full_name} <{u.email}> | role={u.role} | cert={serial}")

    print("\n=== ASSET CATEGORIES ===")
    for c in AssetCategory.query.all():
        print(f"  [{c.id}] {c.name} | risk={c.risk_level}")

    print("\n=== RENTAL ASSETS ===")
    for a in RentalAsset.query.all():
        cat = AssetCategory.query.get(a.category_id)
        print(f"  [{a.id}] {a.asset_title} | cat={cat.name if cat else '?'} | location={a.location} | status={a.status} | owner_id={a.owner_id}")

    print("\n=== AGREEMENT REQUESTS ===")
    for r in AgreementRequest.query.all():
        uid = r.request_uid[:14] + "..." if r.request_uid else "?"
        print(f"  [{r.id}] {uid} | tenant={r.tenant_id} landlord={r.landlord_id} | cat={r.rental_category} | rent={r.proposed_rent} {r.currency} | status={r.status}")

    print("\n=== RENTAL AGREEMENTS ===")
    for ag in RentalAgreement.query.all():
        uid = ag.agreement_uid[:14] + "..." if ag.agreement_uid else "?"
        h = ag.document_hash_sha256[:20] + "..." if ag.document_hash_sha256 else "none"
        lsig = "YES" if ag.landlord_signature else "NO"
        tsig = "YES" if ag.tenant_signature else "NO"
        print(f"  [{ag.id}] {uid} | landlord={ag.landlord_id} tenant={ag.tenant_id} | cat={ag.rental_category} | status={ag.status} | rent={ag.rent_amount} {ag.currency}")
        print(f"       hash={h} | landlord_sig={lsig} | tenant_sig={tsig} | verif_code={ag.verification_code}")

    print("\n=== CHAT THREADS ===")
    for t in ChatThread.query.all():
        msgs = ChatMessage.query.filter_by(thread_id=t.id).count()
        has_key = "YES" if t.encrypted_thread_key else "NO"
        print(f"  [{t.id}] request_id={t.request_id} | messages={msgs} | encrypted_key={has_key}")

    print("\n=== CHAT MESSAGES (last 5) ===")
    for m in ChatMessage.query.order_by(ChatMessage.id.desc()).limit(5).all():
        sender = User.query.get(m.sender_id)
        name = sender.full_name if sender else "unknown"
        sys_flag = "[SYSTEM] " if m.is_system else ""
        print(f"  [{m.id}] thread={m.thread_id} | from={name} | {sys_flag}ciphertext_len={len(m.ciphertext_b64)} | sent={m.sent_at}")

    print("\n=== IDENTITY PHOTOS ===")
    for p in IdentityPhoto.query.all():
        h = p.photo_hash_sha256[:20] + "..." if p.photo_hash_sha256 else "none"
        print(f"  [{p.id}] user_id={p.user_id} | agreement_id={p.agreement_id} | consent={p.consent_given} | hash={h}")

    print("\n=== GENERATED PDFs ===")
    for pdf in GeneratedPDF.query.all():
        h = pdf.pdf_hash_sha256[:20] + "..." if pdf.pdf_hash_sha256 else "none"
        print(f"  [{pdf.id}] agreement_id={pdf.agreement_id} | path={pdf.pdf_file_path} | hash={h}")
