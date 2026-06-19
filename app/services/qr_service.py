import os
import uuid
import qrcode
from pathlib import Path


def generate_qr_code(verification_url, output_dir, code):
    """Generate a QR code image for the given URL. Returns file path."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"qr_{code}.png"
    filepath = os.path.join(output_dir, filename)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    return filepath


def generate_verification_code():
    return uuid.uuid4().hex.upper()
