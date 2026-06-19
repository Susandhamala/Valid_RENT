"""
In-app encrypted chat — REST endpoints used via fetch() for real-time feel.
"""
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.chat import ChatThread, ChatMessage
from app.services.chat_service import (
    encrypt_message, decrypt_thread_messages, generate_thread_key
)

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


def _assert_access(thread: ChatThread):
    req_obj = thread.request
    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        abort(403)


def _reset_thread_key(thread: ChatThread):
    """Replace a corrupt thread key with a fresh one (drops all old messages)."""
    ChatMessage.query.filter_by(thread_id=thread.id).delete()
    thread.encrypted_thread_key = generate_thread_key()
    db.session.commit()


@chat_bp.route('/thread/<int:thread_id>/messages')
@csrf.exempt
@login_required
def get_messages(thread_id):
    thread = ChatThread.query.get_or_404(thread_id)
    _assert_access(thread)
    since_id = request.args.get('since', 0, type=int)
    try:
        msgs = [m for m in decrypt_thread_messages(thread) if m['id'] > since_id]
    except Exception:
        _reset_thread_key(thread)
        msgs = []
    return jsonify({'messages': [
        {
            'id': m['id'],
            'sender_name': m['sender_name'],
            'sender_role': m['sender_role'],
            'text': m['text'],
            'sent_at': m['sent_at'].strftime('%d %b %H:%M'),
            'is_system': m['is_system'],
            'is_mine': m['sender_id'] == current_user.id,
        }
        for m in msgs
    ]})


@chat_bp.route('/thread/<int:thread_id>/send', methods=['POST'])
@csrf.exempt
@login_required
def send_message(thread_id):
    thread = ChatThread.query.get_or_404(thread_id)
    _assert_access(thread)

    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Empty message.'}), 400
    if len(text) > 4000:
        return jsonify({'success': False, 'error': 'Message too long (max 4000 chars).'}), 400

    try:
        ct, nonce, msg_hash = encrypt_message(thread.encrypted_thread_key, text)
    except Exception:
        _reset_thread_key(thread)
        ct, nonce, msg_hash = encrypt_message(thread.encrypted_thread_key, text)

    msg = ChatMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        ciphertext_b64=ct,
        nonce_b64=nonce,
        message_hash=msg_hash,
        is_system=False,
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_name': current_user.full_name,
            'sender_role': current_user.role,
            'text': text,
            'sent_at': msg.sent_at.strftime('%d %b %H:%M'),
            'is_system': False,
            'is_mine': True,
        }
    })
