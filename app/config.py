import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'validrent-dev-secret-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/instance/validrent.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    STORAGE_DIR = BASE_DIR / 'storage'
    AGREEMENTS_DIR = STORAGE_DIR / 'agreements'
    PDFS_DIR = STORAGE_DIR / 'generated_pdfs'
    QR_DIR = STORAGE_DIR / 'qr_codes'
    PHOTOS_DIR = STORAGE_DIR / 'identity_photos'
    ASSET_PHOTOS_DIR = STORAGE_DIR / 'asset_photos'

    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
