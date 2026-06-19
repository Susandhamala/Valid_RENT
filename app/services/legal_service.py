"""
Bilingual legal agreement document generator (English + Nepali).
References: House Rent Act 2053, Contract Act 2056, Electronic Transactions Act 2063, Civil Code 2074.
"""
from jinja2 import Environment, BaseLoader
from app.models.template import LegalDocumentTemplate


_EN_GENERIC = """\
HOUSE RENT / RENTAL AGREEMENT

This Rental Agreement (hereinafter referred to as "Agreement") is made and entered into
on {{ agreement_date }}, in accordance with the House Rent Act, 2053 (1997), the Contract
Act, 2056 (1999), and the Electronic Transactions Act, 2063 (2006) of Nepal, by and between
the following parties:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART I — PARTIES TO THE AGREEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LANDLORD (Party of the First Part):
  Full Name    : {{ landlord_name }}
  Email        : {{ landlord_email }}
  Phone        : {{ landlord_phone }}
  (hereinafter referred to as the "Landlord")

TENANT (Party of the Second Part):
  Full Name    : {{ tenant_name }}
  Email        : {{ tenant_email }}
  Phone        : {{ tenant_phone }}
  (hereinafter referred to as the "Tenant")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART II — PROPERTY / ASSET DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Category        : {{ rental_category }}
  Asset / Property: {{ asset_title }}
  Location/Address: {{ location }}
  Asset ID / No.  : {{ asset_identifier }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART III — TERMS AND CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Article 1 — RENTAL PERIOD
1.1  This Agreement shall commence on {{ start_date }} and shall remain in effect until
     {{ end_date }}, unless lawfully terminated earlier as provided herein.
1.2  This Agreement may be renewed by mutual written consent of both parties, provided that
     notice of intent to renew is given at least 30 (thirty) days prior to expiry.
1.3  Continued occupation of the property by the Tenant after the expiry date, without a
     written renewal, shall not imply automatic renewal.

Article 2 — RENT AND PAYMENT
2.1  The Tenant agrees to pay a rent of {{ currency }} {{ rent_amount }} for the agreed
     rental period, as negotiated and finalized through the Valid Rent platform.
2.2  Rent shall be due and payable on or before the 7th day (Saptami) of each Nepali
     calendar month, as per Section 5 of the House Rent Act, 2053.
2.3  Payment shall be made via the mode mutually agreed upon by both parties. The Landlord
     shall provide a written receipt (Bhuktani Rasid) upon each payment.
2.4  Failure to pay rent within 15 (fifteen) days of the due date shall constitute a
     material breach of this Agreement, entitling the Landlord to initiate proceedings
     under Section 8 of the House Rent Act, 2053.
2.5  Any proposed increase in rent shall be notified at least 35 (thirty-five) days in
     advance, in accordance with the House Rent Act, 2053.

Article 3 — SECURITY DEPOSIT
3.1  The Tenant shall deposit a security amount equivalent to a minimum of one (1) and
     a maximum of three (3) months' rent prior to taking possession of the property.
3.2  The security deposit shall be held by the Landlord and refunded within 15 (fifteen)
     days of the Tenant vacating the property, after deducting verified costs for:
     (a) unpaid rent; (b) damages beyond normal wear and tear; (c) unpaid utility bills.
3.3  Wrongful withholding of the security deposit shall entitle the Tenant to seek redress
     under the Contract Act, 2056 and the Consumer Protection Act, 2075.

Article 4 — OBLIGATIONS OF THE TENANT
4.1  The Tenant shall use the property solely for the agreed and lawful purpose and shall
     not conduct any illegal, immoral, or commercially unregistered activities therein.
4.2  The Tenant shall not sub-let, assign, mortgage, or otherwise transfer possession of
     the property or any part thereof to any third party without prior written consent of
     the Landlord, as required under Section 10 of the House Rent Act, 2053.
4.3  The Tenant shall maintain the property in clean and habitable condition throughout
     the tenancy period, and shall return it in substantially the same condition.
4.4  The Tenant shall be solely responsible for any damages to the property caused by
     negligence, misuse, or unauthorized alteration beyond normal wear and tear.
4.5  The Tenant shall not make any structural modifications, constructions, or alterations
     to the property without the Landlord's prior written approval.
4.6  The Tenant shall pay all applicable utility bills (electricity, water, internet, etc.)
     punctually and shall not allow arrears to accumulate.
4.7  The Tenant shall comply with all applicable local laws, building bylaws, municipal
     regulations, and shall not disturb the peace of neighboring residents.

Article 5 — OBLIGATIONS OF THE LANDLORD
5.1  The Landlord warrants that the property is in habitable condition, free from major
     structural defects, and fit for the agreed purpose at the time of handover.
5.2  The Landlord shall be responsible for all major structural repairs and maintenance
     that are not attributable to the Tenant's negligence or misuse.
5.3  The Landlord shall not interfere with the Tenant's peaceful enjoyment and use of
     the property during the valid tenancy period.
5.4  The Landlord shall ensure that the property is free from any encumbrances or legal
     disputes that would affect the Tenant's quiet possession.
5.5  The Landlord shall comply with all provisions of the House Rent Act, 2053, and shall
     not arbitrarily evict the Tenant without following due legal process.
5.6  The Landlord shall provide access to essential utilities and common facilities as
     agreed and shall not disconnect these services to coerce the Tenant.

Article 6 — TERMINATION OF AGREEMENT
6.1  Either party may terminate this Agreement by providing a written notice of at least
     thirty-five (35) days, as prescribed under Section 7 of the House Rent Act, 2053.
6.2  In the event of material breach by the Tenant (non-payment of rent, illegal use,
     unauthorized sub-letting, or causing serious damage), the Landlord may initiate
     eviction proceedings through the designated Rent Hearing Committee.
6.3  In the event of material breach by the Landlord (unlawful eviction, disconnection
     of utilities, failure to carry out essential repairs), the Tenant may seek redress
     before the Rent Hearing Committee or the District Court.
6.4  Upon termination, the Tenant shall vacate the property and return all keys, access
     cards, and documents within the notice period. Holdover beyond this period shall
     attract a penalty as agreed or as directed by the competent authority.

Article 7 — DISPUTE RESOLUTION
7.1  In case of any dispute, difference, or claim arising out of or in connection with
     this Agreement, the parties shall first attempt amicable resolution through
     direct negotiation within 15 (fifteen) days of the dispute arising.
7.2  If direct negotiation fails, the matter shall be referred to the House Rent Complaint
     Hearing Committee constituted under Section 14 of the House Rent Act, 2053.
7.3  Matters not covered by the House Rent Act, 2053 shall be governed by the Contract
     Act, 2056 (1999) and the Civil Code (Muluki Dewani Sanhita), 2074 of Nepal.
7.4  The parties agree that the courts of Nepal shall have exclusive jurisdiction over
     any legal proceedings arising from this Agreement.

Article 8 — DIGITAL SIGNATURE AND LEGAL VALIDITY
8.1  This Agreement has been digitally signed by both parties using RSA-2048 asymmetric
     cryptography and SHA-256 document hashing.
8.2  Each party's digital signature constitutes a legally valid electronic signature under
     Section 7 of the Electronic Transactions Act, 2063 (2006) of Nepal, and is equivalent
     to a handwritten signature for the purposes of this Agreement.
8.3  The SHA-256 cryptographic hash of this document serves as tamper-evidence. Any
     alteration of the document after signing will be detectable by hash mismatch.
8.4  The X.509 digital certificates of both parties are issued by the Valid Rent Platform
     and serve as proof of identity for the purposes of this Agreement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART IV — FINAL AGREED TERMS & CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The following terms were mutually agreed and recorded by both parties at the time of
digital signing on the Valid Rent platform. These constitute the final, binding conditions
of this Agreement in addition to the standard provisions above.

Landlord's Final Terms ({{ landlord_name }}):
{{ landlord_remarks }}

Tenant's Acceptance & Conditions ({{ tenant_name }}):
{{ tenant_remarks }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART V — DIGITAL VERIFICATION RECORD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Document SHA-256 Hash : {{ document_hash }}
  Verification Code     : {{ verification_code }}
  Platform              : Valid Rent — Secure Rental Agreement Platform
  Legal Framework       : House Rent Act 2053 | Contract Act 2056 | E-Transactions Act 2063
                          Civil Code (Muluki Dewani Sanhita) 2074

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART VI — LEGAL DECLARATION & BINDING EFFECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEGAL VALIDITY STATEMENT:

This Rental Agreement has been voluntarily entered into by both parties with full knowledge,
free consent, and legal capacity as required under Sections 10–14 of the Contract Act, 2056.

By affixing their RSA-2048 digital signatures to this document, both the Landlord and the
Tenant confirm that:

  (i)   They have read, understood, and accepted all terms and conditions herein;
  (ii)  Their digital signature constitutes a legally binding electronic signature under
        Section 7 of the Electronic Transactions Act, 2063;
  (iii) This Agreement is enforceable in the courts of Nepal with the same legal force
        as a physically signed document under the Civil Code, 2074;
  (iv)  The SHA-256 cryptographic hash serves as tamper-evidence — any post-signing
        modification is detectable and renders this Agreement void;
  (v)   Their identity has been verified through government-issued documents submitted
        on the Valid Rent platform and is on record.

THIS AGREEMENT IS FULLY VALID AND LEGALLY BINDING FROM THE DATE OF BOTH PARTIES'
DIGITAL SIGNATURES. EITHER PARTY MAY SEEK ENFORCEMENT BEFORE THE RENT HEARING
COMMITTEE (House Rent Act 2053, Section 14) OR THE DISTRICT COURT OF NEPAL.

Both parties hereby declare that they have not been coerced, misled, or induced into
signing this Agreement, and that all representations made herein are true and accurate
to the best of their knowledge.

Executed electronically on the Valid Rent Secure Platform.
"""


_NP_GENERIC = """\
घर भाडा / बहाल सम्झौता

यो भाडा सम्झौता (यसपछि "सम्झौता" भनिनेछ) घर बहाल ऐन, २०५३, करार ऐन, २०५६ र
इलेक्ट्रोनिक कारोबार ऐन, २०६३ बमोजिम मिति {{ agreement_date }} मा निम्न पक्षहरू बीच
सम्पन्न भएको छ:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग १ — पक्षहरूको परिचय
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

घर मालिक (पहिलो पक्ष):
  पूरा नाम : {{ landlord_name }}
  इमेल     : {{ landlord_email }}
  फोन      : {{ landlord_phone }}
  (यसपछि "घर मालिक" भनिनेछ)

भाडावाला (दोस्रो पक्ष):
  पूरा नाम : {{ tenant_name }}
  इमेल     : {{ tenant_email }}
  फोन      : {{ tenant_phone }}
  (यसपछि "भाडावाला" भनिनेछ)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग २ — सम्पत्तिको विवरण
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  वर्ग              : {{ rental_category }}
  सम्पत्तिको नाम    : {{ asset_title }}
  ठेगाना / स्थान    : {{ location }}
  सम्पत्ति परिचय नं.: {{ asset_identifier }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग ३ — सर्त तथा शर्तहरू
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

धारा १ — भाडा अवधि
१.१  यो सम्झौता मिति {{ start_date }} देखि लागू भई {{ end_date }} मा समाप्त हुनेछ।
१.२  सम्झौता नवीकरण गर्नु परेमा म्याद सकिनु अघि कम्तिमा ३० दिन अगाडि लिखित
     सहमति जनाउनु पर्नेछ।
१.३  म्याद सकिएपछि लिखित नवीकरण बिना भाडावालाले थप समय बस्नुले स्वतः नवीकरण
     भएको मानिने छैन।

धारा २ — भाडा र भुक्तानी
२.१  भाडावाला सहमत बमोजिम {{ currency }} {{ rent_amount }} भाडा तिर्न सहमत छन्।
२.२  भाडा घर बहाल ऐन, २०५३ को दफा ५ बमोजिम प्रत्येक महिनाको सप्तमीभित्र
     तिर्नु पर्नेछ।
२.३  घर मालिकले प्रत्येक भुक्तानीमा भुक्तानी रसिद उपलब्ध गराउनु पर्नेछ।
२.४  भाडा तिर्न १५ दिनभन्दा बढी ढिला गरेमा सम्झौता उल्लंघन मानी घर बहाल ऐन,
     २०५३ को दफा ८ अन्तर्गत कारबाही हुन सक्नेछ।
२.५  भाडा वृद्धि गर्नु परेमा कम्तिमा ३५ दिन अगाडि लिखित सूचना दिनु पर्नेछ।

धारा ३ — धरौटी रकम
३.१  भाडावालाले सम्पत्ति बुझिनु अगाडि कम्तिमा एक (१) महिनाको भाडा बराबर
     धरौटी रकम जम्मा गर्नु पर्नेछ।
३.२  सम्पत्ति खाली गरेको १५ दिनभित्र धरौटी फिर्ता गरिनेछ। अनुचित विलम्ब
     भएमा करार ऐन, २०५६ बमोजिम क्षतिपूर्ति माग गर्न सकिनेछ।

धारा ४ — भाडावालाका दायित्वहरू
४.१  भाडावालाले सम्पत्तिलाई केवल सहमत र कानूनी उद्देश्यका लागि मात्र प्रयोग
     गर्नु पर्नेछ।
४.२  घर बहाल ऐन, २०५३ को दफा १० बमोजिम घर मालिकको लिखित अनुमतिबिना
     सम्पत्ति अर्कोलाई भाडामा दिन, हस्तान्तरण गर्न वा धितो राख्न पाइँदैन।
४.३  भाडावालाले सम्पत्तिलाई सफा र राम्रो अवस्थामा राख्नु पर्नेछ।
४.४  भाडावालाको लापरवाहीले भएको क्षतिको जिम्मेवारी भाडावालाकै हुनेछ।
४.५  घर मालिकको अनुमतिबिना संरचनात्मक परिवर्तन गर्न पाइँदैन।
४.६  बिजुली, पानी लगायतका उपयोगिता बिलहरू समयमै तिर्नु पर्नेछ।
४.७  सबै लागू हुने स्थानीय कानून र नियमहरूको पालना गर्नु पर्नेछ।

धारा ५ — घर मालिकका दायित्वहरू
५.१  घर मालिकले सम्पत्ति बसोबासयोग्य र दोषमुक्त अवस्थामा हस्तान्तरण गर्नु पर्नेछ।
५.२  ठूला संरचनात्मक मर्मत तथा सुधारको जिम्मेवारी घर मालिकको हुनेछ।
५.३  घर मालिकले भाडावालाको शान्तिपूर्ण बसोबासमा हस्तक्षेप गर्न पाइँदैन।
५.४  कानूनी प्रक्रिया अपनाएर मात्र बेदखल गर्न सकिनेछ। अन्यथा बेदखल गर्नु
     घर बहाल ऐन, २०५३ को उल्लंघन मानिनेछ।
५.५  आवश्यक उपयोगिता सेवाहरू उपलब्ध गराउनु पर्नेछ र जबर्जस्ती हटाउन पाइँदैन।

धारा ६ — सम्झौता अन्त्य
६.१  घर बहाल ऐन, २०५३ को दफा ७ बमोजिम कुनै पनि पक्षले ३५ दिनको लिखित सूचना
     दिई सम्झौता अन्त्य गर्न सक्नेछ।
६.२  भाडावालाले सम्झौता उल्लंघन गरेमा घर बहाल उजुरी सुन्ने समिति समक्ष
     बेदखल उजुरी गर्न सकिनेछ।
६.३  सम्झौता अन्त्यमा भाडावालाले सबै साँचो र पहुँच उपकरणहरू फिर्ता गरी
     सम्पत्ति खाली गर्नु पर्नेछ।

धारा ७ — विवाद समाधान
७.१  कुनै विवाद उत्पन्न भएमा पहिले आपसी सहमतिद्वारा १५ दिनभित्र समाधान
     गर्ने प्रयास गरिनेछ।
७.२  समाधान नभएमा घर बहाल ऐन, २०५३ को दफा १४ अन्तर्गत गठित घर बहाल उजुरी
     सुन्ने समिति समक्ष पेश गरिनेछ।
७.३  घर बहाल ऐनले नसमेटेका विषयहरूमा करार ऐन, २०५६ र मुलुकी देवानी संहिता,
     २०७४ लागू हुनेछ।
७.४  नेपालका अदालतहरूले यस सम्झौतासम्बन्धी विवादमा एकल अधिकारक्षेत्र राख्नेछन्।

धारा ८ — डिजिटल हस्ताक्षर र कानूनी वैधता
८.१  यो सम्झौता RSA-2048 असममित क्रिप्टोग्राफी र SHA-256 ह्यासिङद्वारा
     सुरक्षित गरिएको छ।
८.२  इलेक्ट्रोनिक कारोबार ऐन, २०६३ को दफा ७ बमोजिम प्रत्येक पक्षको डिजिटल
     हस्ताक्षर हस्तलिखित हस्ताक्षरसरह कानूनी मान्यता राख्छ।
८.३  SHA-256 क्रिप्टोग्राफिक ह्यासले कागजातको अखण्डता सुनिश्चित गर्छ। हस्ताक्षर
     पछि कागजातमा कुनै परिवर्तन भएमा ह्यास भेट हुने छैन।

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग ४ — अन्तिम सहमत सर्तहरू
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

डिजिटल हस्ताक्षरको समयमा भ्यालिड रेन्ट प्लेटफर्ममा दुवै पक्षले आपसी सहमतिमा दर्ज गरेका
निम्न सर्तहरू यस सम्झौताका मानक प्रावधानहरूका अतिरिक्त अन्तिम, बाध्यकारी सर्त हुन्।

घर मालिकको अन्तिम सर्तहरू ({{ landlord_name }}):
{{ landlord_remarks }}

भाडावालाको स्वीकृति र सर्तहरू ({{ tenant_name }}):
{{ tenant_remarks }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग ५ — डिजिटल प्रमाणीकरण अभिलेख
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  कागजात SHA-256 ह्यास : {{ document_hash }}
  प्रमाणीकरण कोड       : {{ verification_code }}
  प्लेटफर्म             : भ्यालिड रेन्ट — सुरक्षित भाडा सम्झौता प्लेटफर्म
  कानूनी आधार          : घर बहाल ऐन २०५३ | करार ऐन २०५६ | इलेक्ट्रोनिक कारोबार ऐन २०६३
                          मुलुकी देवानी संहिता २०७४

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
भाग ६ — कानूनी घोषणा र बाध्यकारी प्रभाव
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

कानूनी वैधताको विवरण:

यो भाडा सम्झौता करार ऐन, २०५६ को दफा १०–१४ अन्तर्गत आवश्यक पूर्ण ज्ञान, स्वतन्त्र
सहमति र कानूनी क्षमतासहित दुवै पक्षले स्वेच्छाले प्रवेश गरेको हो।

यस कागजातमा RSA-2048 डिजिटल हस्ताक्षर गरेर घर मालिक र भाडावाला दुवैले पुष्टि गर्दछन्:

  (i)   उनीहरूले यहाँका सबै सर्त र शर्तहरू पढी, बुझी र स्वीकार गरेका छन्;
  (ii)  उनीहरूको डिजिटल हस्ताक्षर इलेक्ट्रोनिक कारोबार ऐन, २०६३ को दफा ७ अन्तर्गत
        कानूनी रूपमा बाध्यकारी इलेक्ट्रोनिक हस्ताक्षर हो;
  (iii) यो सम्झौता मुलुकी देवानी संहिता, २०७४ अन्तर्गत भौतिक हस्ताक्षर गरिएको
        कागजातसरह समान कानूनी बल सहित नेपालका अदालतहरूमा लागू गर्न सकिन्छ;
  (iv)  SHA-256 क्रिप्टोग्राफिक ह्यासले छेडछाड प्रमाण गर्छ — हस्ताक्षरपछिको कुनै
        परिवर्तन पत्ता लगाउन सकिन्छ र सम्झौतालाई अमान्य बनाउँछ;
  (v)   भ्यालिड रेन्ट प्लेटफर्ममा पेश गरिएका सरकारी कागजातहरूद्वारा उनीहरूको पहिचान
        प्रमाणित गरिएको छ र अभिलेखमा सुरक्षित राखिएको छ।

दुवै पक्षको डिजिटल हस्ताक्षरको मितिदेखि यो सम्झौता पूर्ण रूपमा वैध र कानूनी रूपमा
बाध्यकारी छ। कुनै पनि पक्षले घर बहाल ऐन, २०५३ को दफा १४ अन्तर्गत गठित घर बहाल उजुरी
सुन्ने समिति वा नेपालको जिल्ला अदालत समक्ष लागू गर्न माग गर्न सक्नेछ।

दुवै पक्षले घोषणा गर्दछन् कि उनीहरूलाई जबर्जस्ती वा भुलाएर सम्झौता गराइएको छैन र
यहाँ उल्लिखित सबै विवरणहरू उनीहरूको जानकारी र विश्वासअनुसार सत्य र सहीछन्।

भ्यालिड रेन्ट सुरक्षित प्लेटफर्ममा डिजिटल रूपमा सम्पादित।
"""


_CATEGORY_OVERRIDES = {
    'Land': {
        'en': _EN_GENERIC.replace('PROPERTY / ASSET DESCRIPTION', 'LAND / PLOT DESCRIPTION')
                          .replace('The Tenant shall maintain the property in clean and habitable condition',
                                   'The Tenant shall use the land only for the agreed purpose and maintain its boundaries'),
        'np': _NP_GENERIC.replace('सम्पत्तिको विवरण', 'जग्गा / प्लटको विवरण'),
    },
    'Automobile': {
        'en': _EN_GENERIC.replace('PROPERTY / ASSET DESCRIPTION', 'VEHICLE DESCRIPTION')
                          .replace('The Tenant shall maintain the property in clean and habitable condition',
                                   'The Tenant shall return the vehicle in its original condition with a full fuel tank'),
        'np': _NP_GENERIC.replace('सम्पत्तिको विवरण', 'सवारी साधनको विवरण'),
    },
}


def _render(template_str: str, context: dict) -> str:
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(template_str)
    return tmpl.render(**context)


def get_template_for_category(category: str) -> tuple[str, str]:
    db_tmpl = LegalDocumentTemplate.query.filter_by(
        category=category, is_active=True).first()
    if db_tmpl:
        return db_tmpl.template_en, db_tmpl.template_np
    override = _CATEGORY_OVERRIDES.get(category)
    if override:
        return override['en'], override['np']
    return _EN_GENERIC, _NP_GENERIC


def generate_bilingual_document(request, agreement=None) -> tuple[str, str]:
    from datetime import date
    asset = request.asset

    context = {
        'agreement_date': date.today().strftime('%d %B %Y'),
        'landlord_name': request.landlord.full_name,
        'landlord_email': request.landlord.email,
        'landlord_phone': getattr(request.landlord, 'phone', None) or 'N/A',
        'tenant_name': request.tenant.full_name,
        'tenant_email': request.tenant.email,
        'tenant_phone': getattr(request.tenant, 'phone', None) or 'N/A',
        'rental_category': request.rental_category,
        'asset_title': asset.asset_title if asset else 'N/A',
        'location': asset.location if asset else 'N/A',
        'asset_identifier': asset.asset_identifier if asset else 'N/A',
        'start_date': str(request.proposed_start_date or 'TBD'),
        'end_date': str(request.proposed_end_date or 'TBD'),
        'currency': request.currency,
        'rent_amount': f"{request.effective_rent:,.2f}" if request.effective_rent else 'TBD',
        'landlord_remarks': (agreement.landlord_remarks if agreement else None) or 'Not specified.',
        'tenant_remarks': (agreement.tenant_remarks if agreement else None) or 'Not specified.',
        'document_hash': agreement.document_hash_sha256 if agreement else 'Pending',
        'verification_code': agreement.verification_code if agreement else 'Pending',
    }

    en_tmpl, np_tmpl = get_template_for_category(request.rental_category)
    return _render(en_tmpl, context), _render(np_tmpl, context)
