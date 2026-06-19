from app.extensions import db

from app.models.user import User
from app.models.certificate import Certificate
from app.models.asset import AssetCategory, RentalAsset
from app.models.agreement import RentalAgreement
from app.models.photo import IdentityPhoto
from app.models.pdf import GeneratedPDF
from app.models.request import AgreementRequest, PartyApproval
from app.models.chat import ChatThread, ChatMessage
from app.models.template import LegalDocumentTemplate
