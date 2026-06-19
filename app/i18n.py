"""
Multi-language translation strings for Valid Rent.
Add new languages by adding a new top-level key.
"""

SUPPORTED = {
    'en': 'English',
    'ne': 'नेपाली',
}

TRANSLATIONS = {

    # ── ENGLISH ──────────────────────────────────────────────────
    'en': {
        # brand
        'brand_name': 'ValidRent',
        'brand_sub': 'Secure Platform',
        'tagline': "Nepal's Secure Multi-Category Rental Verification Platform",

        # nav
        'nav_dashboard': 'Dashboard',
        'nav_requests': 'Requests',
        'nav_agreements': 'Agreements',
        'nav_assets': 'My Assets',
        'nav_new_agreement': 'New Agreement',
        'nav_browse': 'Browse Assets',
        'nav_crypto': 'Cryptography',
        'nav_logout': 'Logout',

        # topbar
        'page_dashboard': 'Dashboard',

        # dashboard
        'hello': 'Hello',
        'account': 'Account',
        'btn_new_asset': '+ New Asset',
        'btn_new_agreement': '+ New Agreement',
        'btn_browse': '🔍 Browse Available Rentals',
        'pending_requests_alert': 'new rental request(s) waiting for your review',
        'from': 'From',
        'btn_review_now': 'Review Now →',
        'stat_total_agreements': 'Total Agreements',
        'stat_verified': 'Verified',
        'stat_pending': 'Pending',
        'stat_assets': 'Assets Listed',
        'stat_new_requests': 'New Requests',
        'stat_my_requests': 'My Requests',
        'your_cert': 'Your Digital Certificate',
        'cert_issued_by': 'Issued by Valid Rent Demo CA — X.509 Standard',
        'cert_valid': 'Valid',
        'cert_revoked': 'Revoked',
        'cert_expired': 'Expired',
        'cert_serial': 'Serial Number',
        'cert_expires': 'Expires',
        'cert_issued': 'Issued',
        'cert_subject': 'Subject',
        'no_cert': 'No certificate found. Please contact support or re-register.',
        'recent_agreements': 'Recent Agreements',
        'recent_agreements_sub': 'Your latest rental agreements',
        'btn_view_all': 'View All',
        'col_agreement_id': 'Agreement ID',
        'col_category': 'Category',
        'col_tenant': 'Tenant',
        'col_landlord': 'Landlord',
        'col_rent': 'Rent',
        'col_status': 'Status',
        'col_actions': 'Actions',
        'btn_view': 'View',
        'no_agreements': 'No agreements yet',
        'no_agreements_landlord': 'Create your first agreement →',
        'no_agreements_tenant': 'Wait for a landlord to add you to an agreement.',
        'my_assets': 'My Assets',
        'my_assets_sub': 'Rental assets you have listed',
        'col_asset': 'Asset',
        'col_location': 'Location',
        'status_available': 'Available',
        'status_rented': 'Rented',

        # auth - login
        'login_welcome': 'Welcome back',
        'login_sub': 'Sign in to your secure account',
        'label_email': 'Email Address',
        'label_password': 'Password',
        'label_remember': 'Keep me signed in',
        'btn_signin': 'Sign In',
        'login_no_account': "Don't have an account?",
        'login_create': 'Create one',
        'academic_note': 'Academic Prototype — Not affiliated with the Government of Nepal. For educational purposes only.',

        # auth - register
        'register_title': 'Create account',
        'register_sub': 'Your RSA key pair and digital certificate will be generated automatically.',
        'label_fullname': 'Full Name',
        'label_phone': 'Phone Number',
        'label_role': 'I am a',
        'role_landlord': 'Landlord',
        'role_landlord_sub': 'I own assets to rent',
        'role_tenant': 'Tenant',
        'role_tenant_sub': 'I want to rent',
        'label_confirm_password': 'Confirm Password',
        'btn_create_account': 'Create Account & Get Certificate',
        'register_have_account': 'Already have an account?',
        'register_signin': 'Sign in',
        'register_tagline': 'Create your account and get your digital certificate instantly.',

        # browse assets
        'browse_title': 'Browse Rental Listings',
        'browse_hero_title': 'Find Your Perfect Rental',
        'browse_hero_sub': 'Browse verified, secure rental listings. All agreements are digitally signed.',
        'search_placeholder': 'Search by title or location...',
        'all_categories': 'All Categories',
        'listings_found': 'listings found',
        'no_listings': 'No listings found',
        'no_listings_sub': 'Try adjusting your search or category filter.',
        'btn_request': '📋 Request Rental',
        'btn_contact': 'Contact',
        'by_landlord': 'Listed by',
        'label_location': 'Location',
        'label_price': 'Price',
        'per_month': '/month',

        # requests
        'requests_title': 'Rental Requests',
        'my_requests': 'My Requests',
        'incoming_requests': 'Incoming Requests',
        'new_request': 'New Rental Request',
        'request_details': 'Request Details',
        'label_start_date': 'Start Date',
        'label_end_date': 'End Date',
        'label_offered_rent': 'Offered Rent',
        'label_message': 'Message to Landlord',
        'btn_submit_request': 'Submit Request',
        'status_pending': 'Pending',
        'status_under_review': 'Under Review',
        'status_negotiating': 'Negotiating',
        'status_approved': 'Approved',
        'status_rejected': 'Rejected',
        'status_agreement_created': 'Agreement Created',

        # agreements
        'agreements_title': 'Agreements',
        'create_agreement': 'Create Agreement',

        # photos
        'photo_capture_title': 'Identity Photo Capture',
        'photo_consent': 'I consent to my photo being used as identity evidence for this rental agreement.',
        'btn_capture': 'Capture Photo',
        'btn_retake': 'Retake',
        'btn_save_photo': 'Save Photo',

        # chat
        'chat_title': 'Encrypted Chat',
        'chat_placeholder': 'Type a message...',
        'btn_send': 'Send',

        # general
        'btn_back': '← Back',
        'btn_cancel': 'Cancel',
        'btn_save': 'Save',
        'btn_submit': 'Submit',
        'btn_download': 'Download PDF',
        'btn_sign': 'Sign Agreement',
        'btn_approve': 'Approve',
        'btn_reject': 'Reject',
        'loading': 'Loading...',
        'yes': 'Yes',
        'no': 'No',

        # crypto page
        'crypto_title': 'Where Each Algorithm Is Used',
        'crypto_sub': 'Every encryption, signature, and hash call — with the exact file path and line number.',

        # verification
        'verify_valid': 'VALID',
        'verify_invalid': 'INVALID',
        'verify_title': 'Agreement Verification',
    },

    # ── नेपाली ────────────────────────────────────────────────────
    'ne': {
        # brand
        'brand_name': 'भ्यालिडरेन्ट',
        'brand_sub': 'सुरक्षित मञ्च',
        'tagline': 'नेपालको सुरक्षित बहु-श्रेणी भाडा प्रमाणीकरण मञ्च',

        # nav
        'nav_dashboard': 'ड्यासबोर्ड',
        'nav_requests': 'अनुरोधहरू',
        'nav_agreements': 'सम्झौताहरू',
        'nav_assets': 'मेरा सम्पत्तिहरू',
        'nav_new_agreement': 'नयाँ सम्झौता',
        'nav_browse': 'सम्पत्ति हेर्नुहोस्',
        'nav_crypto': 'क्रिप्टोग्राफी',
        'nav_logout': 'बाहिर निस्कनुहोस्',

        # topbar
        'page_dashboard': 'ड्यासबोर्ड',

        # dashboard
        'hello': 'नमस्ते',
        'account': 'खाता',
        'btn_new_asset': '+ नयाँ सम्पत्ति',
        'btn_new_agreement': '+ नयाँ सम्झौता',
        'btn_browse': '🔍 उपलब्ध भाडाहरू हेर्नुहोस्',
        'pending_requests_alert': 'नयाँ भाडा अनुरोध(हरू) तपाईंको समीक्षाको प्रतीक्षामा छन्',
        'from': 'बाट',
        'btn_review_now': 'अहिले समीक्षा गर्नुहोस् →',
        'stat_total_agreements': 'कुल सम्झौताहरू',
        'stat_verified': 'प्रमाणित',
        'stat_pending': 'विचाराधीन',
        'stat_assets': 'सूचीबद्ध सम्पत्तिहरू',
        'stat_new_requests': 'नयाँ अनुरोधहरू',
        'stat_my_requests': 'मेरा अनुरोधहरू',
        'your_cert': 'तपाईंको डिजिटल प्रमाणपत्र',
        'cert_issued_by': 'भ्यालिड रेन्ट डेमो CA द्वारा जारी — X.509 मानक',
        'cert_valid': 'मान्य',
        'cert_revoked': 'रद्द गरिएको',
        'cert_expired': 'म्याद सकिएको',
        'cert_serial': 'क्रम संख्या',
        'cert_expires': 'म्याद सकिने मिति',
        'cert_issued': 'जारी मिति',
        'cert_subject': 'विषय',
        'no_cert': 'प्रमाणपत्र फेला परेन। कृपया सहायताको लागि सम्पर्क गर्नुहोस् वा पुनः दर्ता गर्नुहोस्।',
        'recent_agreements': 'हालका सम्झौताहरू',
        'recent_agreements_sub': 'तपाईंका ताजा भाडा सम्झौताहरू',
        'btn_view_all': 'सबै हेर्नुहोस्',
        'col_agreement_id': 'सम्झौता आईडी',
        'col_category': 'श्रेणी',
        'col_tenant': 'भाडावाल',
        'col_landlord': 'घरधनी',
        'col_rent': 'भाडा',
        'col_status': 'स्थिति',
        'col_actions': 'कार्यहरू',
        'btn_view': 'हेर्नुहोस्',
        'no_agreements': 'अहिलेसम्म कुनै सम्झौता छैन',
        'no_agreements_landlord': 'पहिलो सम्झौता सिर्जना गर्नुहोस् →',
        'no_agreements_tenant': 'घरधनीले तपाईंलाई सम्झौतामा थप्नको प्रतीक्षा गर्नुहोस्।',
        'my_assets': 'मेरा सम्पत्तिहरू',
        'my_assets_sub': 'तपाईंले सूचीबद्ध गरेका भाडा सम्पत्तिहरू',
        'col_asset': 'सम्पत्ति',
        'col_location': 'स्थान',
        'status_available': 'उपलब्ध',
        'status_rented': 'भाडामा दिइएको',

        # auth - login
        'login_welcome': 'फिर्ता स्वागत छ',
        'login_sub': 'आफ्नो सुरक्षित खातामा साइन इन गर्नुहोस्',
        'label_email': 'इमेल ठेगाना',
        'label_password': 'पासवर्ड',
        'label_remember': 'साइन इन राख्नुहोस्',
        'btn_signin': 'साइन इन गर्नुहोस्',
        'login_no_account': 'खाता छैन?',
        'login_create': 'बनाउनुहोस्',
        'academic_note': 'शैक्षिक प्रोटोटाइप — नेपाल सरकारसँग सम्बद्ध छैन। शैक्षिक उद्देश्यका लागि मात्र।',

        # auth - register
        'register_title': 'खाता बनाउनुहोस्',
        'register_sub': 'तपाईंको RSA की जोडी र डिजिटल प्रमाणपत्र स्वतः उत्पन्न हुनेछ।',
        'label_fullname': 'पूरा नाम',
        'label_phone': 'फोन नम्बर',
        'label_role': 'म हुँ',
        'role_landlord': 'घरधनी',
        'role_landlord_sub': 'मसँग भाडामा दिने सम्पत्ति छ',
        'role_tenant': 'भाडावाल',
        'role_tenant_sub': 'म भाडामा लिन चाहन्छु',
        'label_confirm_password': 'पासवर्ड पुष्टि गर्नुहोस्',
        'btn_create_account': 'खाता बनाउनुहोस् र प्रमाणपत्र पाउनुहोस्',
        'register_have_account': 'पहिले नै खाता छ?',
        'register_signin': 'साइन इन गर्नुहोस्',
        'register_tagline': 'आफ्नो खाता बनाउनुहोस् र तुरुन्त डिजिटल प्रमाणपत्र पाउनुहोस्।',

        # browse assets
        'browse_title': 'भाडा सूचीहरू हेर्नुहोस्',
        'browse_hero_title': 'आफ्नो आदर्श भाडा खोज्नुहोस्',
        'browse_hero_sub': 'प्रमाणित र सुरक्षित भाडा सूचीहरू हेर्नुहोस्। सबै सम्झौताहरू डिजिटल रूपमा हस्ताक्षरित छन्।',
        'search_placeholder': 'शीर्षक वा स्थानले खोज्नुहोस्...',
        'all_categories': 'सबै श्रेणीहरू',
        'listings_found': 'सूचीहरू फेला परे',
        'no_listings': 'कुनै सूची फेला परेन',
        'no_listings_sub': 'आफ्नो खोज वा श्रेणी फिल्टर समायोजन गर्नुहोस्।',
        'btn_request': '📋 भाडा अनुरोध गर्नुहोस्',
        'btn_contact': 'सम्पर्क गर्नुहोस्',
        'by_landlord': 'सूचीबद्ध गरेकाले',
        'label_location': 'स्थान',
        'label_price': 'मूल्य',
        'per_month': '/महिना',

        # requests
        'requests_title': 'भाडा अनुरोधहरू',
        'my_requests': 'मेरा अनुरोधहरू',
        'incoming_requests': 'आउने अनुरोधहरू',
        'new_request': 'नयाँ भाडा अनुरोध',
        'request_details': 'अनुरोध विवरण',
        'label_start_date': 'सुरु मिति',
        'label_end_date': 'अन्त मिति',
        'label_offered_rent': 'प्रस्तावित भाडा',
        'label_message': 'घरधनीलाई सन्देश',
        'btn_submit_request': 'अनुरोध पठाउनुहोस्',
        'status_pending': 'विचाराधीन',
        'status_under_review': 'समीक्षाधीन',
        'status_negotiating': 'वार्तामा',
        'status_approved': 'स्वीकृत',
        'status_rejected': 'अस्वीकृत',
        'status_agreement_created': 'सम्झौता सिर्जना भयो',

        # agreements
        'agreements_title': 'सम्झौताहरू',
        'create_agreement': 'सम्झौता सिर्जना गर्नुहोस्',

        # photos
        'photo_capture_title': 'पहिचान फोटो खिच्नुहोस्',
        'photo_consent': 'म सहमत छु कि मेरो फोटो यस भाडा सम्झौताको पहिचान प्रमाणको रूपमा प्रयोग हुनेछ।',
        'btn_capture': 'फोटो खिच्नुहोस्',
        'btn_retake': 'पुनः खिच्नुहोस्',
        'btn_save_photo': 'फोटो बचत गर्नुहोस्',

        # chat
        'chat_title': 'एन्क्रिप्टेड च्याट',
        'chat_placeholder': 'सन्देश टाइप गर्नुहोस्...',
        'btn_send': 'पठाउनुहोस्',

        # general
        'btn_back': '← पछाडि',
        'btn_cancel': 'रद्द गर्नुहोस्',
        'btn_save': 'बचत गर्नुहोस्',
        'btn_submit': 'पेश गर्नुहोस्',
        'btn_download': 'PDF डाउनलोड गर्नुहोस्',
        'btn_sign': 'सम्झौतामा हस्ताक्षर गर्नुहोस्',
        'btn_approve': 'स्वीकृत गर्नुहोस्',
        'btn_reject': 'अस्वीकार गर्नुहोस्',
        'loading': 'लोड हुँदैछ...',
        'yes': 'हो',
        'no': 'होइन',

        # crypto page
        'crypto_title': 'प्रत्येक एल्गोरिदम कहाँ प्रयोग गरिएको छ',
        'crypto_sub': 'प्रत्येक इन्क्रिप्सन, हस्ताक्षर र ह्यास कल — सटीक फाइल पाथ र लाइन नम्बरसहित।',

        # verification
        'verify_valid': 'मान्य छ',
        'verify_invalid': 'अमान्य छ',
        'verify_title': 'सम्झौता प्रमाणीकरण',
    },
}


def get_translations(lang: str) -> dict:
    """Return translation dict for the given language code, fallback to English."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en'])
