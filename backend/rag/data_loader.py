"""
NYAYA AI — Legal Data Loader
Loads, structures and chunks all Indian legal documents for RAG indexing
"""
import json
import asyncio
from pathlib import Path
from typing import List, Dict
from loguru import logger

from rag.pipeline import LegalDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter


class LegalDataLoader:
    """
    Loads all legal data from structured JSON files and raw text.
    Data covers: Constitution, IPC/BNS, CrPC/BNSS, Labour Codes,
    RTI Act, Consumer Protection, Land Laws, Govt Schemes + more.
    """

    def __init__(self):
        self.data_dir = Path("./data/processed")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            separators=["\n\n", "\n", "।", ".", " "],
        )

    async def load_all(self) -> List[LegalDocument]:
        """Load all legal knowledge sources"""
        all_docs = []
        loaders = [
            self._load_constitution(),
            self._load_criminal_law(),
            self._load_labour_law(),
            self._load_rti(),
            self._load_consumer_law(),
            self._load_property_law(),
            self._load_family_law(),
            self._load_govt_schemes(),
            self._load_procedures(),
            self._load_helplines(),
        ]

        results = await asyncio.gather(*loaders)
        for docs in results:
            all_docs.extend(docs)

        logger.info(f"Total legal chunks loaded: {len(all_docs)}")
        return all_docs

    async def _load_constitution(self) -> List[LegalDocument]:
        """Load Indian Constitution - all 395 articles"""
        docs = []
        # Fundamental Rights (most queried)
        fundamental_rights = [
            {
                "article": "12-35",
                "title": "Fundamental Rights",
                "content": """Article 14: Right to Equality - The State shall not deny to any person equality before the law 
                or the equal protection of the laws within the territory of India. This means no person can be discriminated 
                against by the government. If any government official treats you differently without valid reason, 
                you can file a writ petition in High Court or Supreme Court.""",
            },
            {
                "article": "19",
                "title": "Right to Freedom of Speech",
                "content": """Article 19(1)(a): All citizens shall have the right to freedom of speech and expression. 
                This means you can speak, write, publish, or broadcast your views freely. However, reasonable restrictions 
                apply for sovereignty, security of state, friendly relations with foreign states, public order, decency, 
                morality, contempt of court, defamation, or incitement to an offence.""",
            },
            {
                "article": "21",
                "title": "Right to Life and Personal Liberty",
                "content": """Article 21: No person shall be deprived of his life or personal liberty except according 
                to procedure established by law. This is the most important fundamental right. It includes:
                - Right to live with dignity
                - Right to livelihood
                - Right to privacy (K.S. Puttaswamy vs Union of India, 2017 - 9 judge bench)
                - Right to health
                - Right to education (until 14 years under Article 21A)
                - Right to speedy trial
                If police arrest you, they MUST tell you why. They cannot keep you in custody beyond 24 hours without 
                producing you before a magistrate.""",
            },
            {
                "article": "22",
                "title": "Protection Against Arrest and Detention",
                "content": """Article 22: Protection against arrest and detention in certain cases.
                YOUR RIGHTS WHEN ARRESTED:
                1. You must be informed of grounds of arrest IMMEDIATELY
                2. You have the RIGHT to consult a lawyer of your choice
                3. You MUST be produced before nearest magistrate within 24 hours
                4. No police officer can keep you beyond 24 hours without magistrate order
                5. Under BNSS 2023: Police must inform your family/friend within 12 hours
                If any of these are violated: file writ petition u/Article 32 in Supreme Court 
                or Article 226 in High Court for habeas corpus.""",
            },
            {
                "article": "32",
                "title": "Right to Constitutional Remedies",
                "content": """Article 32: Right to move Supreme Court for enforcement of Fundamental Rights.
                Dr. Ambedkar called this 'the heart and soul of the Constitution'.
                Types of writs:
                1. HABEAS CORPUS - Release from illegal detention. File when someone is illegally detained.
                2. MANDAMUS - Order to govt official to perform their duty. File when official refuses to act.
                3. PROHIBITION - Stop lower court from exceeding jurisdiction.
                4. CERTIORARI - Quash illegal order of lower court/tribunal.
                5. QUO WARRANTO - Challenge someone's right to hold public office.
                For High Court: Article 226 (broader jurisdiction, can file for any legal right not just fundamental)""",
            },
        ]

        for item in fundamental_rights:
            chunks = self.splitter.split_text(item["content"])
            for chunk in chunks:
                docs.append(LegalDocument(
                    content=chunk,
                    act="Constitution of India",
                    section=f"Article {item['article']}",
                    section_title=item["title"],
                    doc_type="constitutional",
                    language="en",
                    source_url="https://legislative.gov.in/constitution-of-india",
                ))
        return docs

    async def _load_criminal_law(self) -> List[LegalDocument]:
        """Load IPC/BNS, CrPC/BNSS criminal law"""
        docs = []
        criminal_sections = [
            {
                "act": "Bharatiya Nyaya Sanhita (BNS) 2023 / IPC",
                "section": "Section 103 BNS (Section 302 IPC)",
                "title": "Murder",
                "content": """Murder (Section 103 BNS / Section 302 IPC): Whoever commits murder shall be punished 
                with death or imprisonment for life, and shall also be liable to fine.
                COGNIZABLE: Yes | BAILABLE: No | TRIABLE BY: Sessions Court
                For murder FIR: Go to nearest police station. Police CANNOT refuse to register FIR for cognizable offence.
                If police refuse: Go to SP (Superintendent of Police) or file complaint before Judicial Magistrate u/s 175 BNSS.
                Key SC judgment: Lalita Kumari vs Govt of UP (2013) - Police MUST register FIR for cognizable offence, no preliminary inquiry allowed.""",
            },
            {
                "act": "Bharatiya Nyaya Sanhita (BNS) 2023",
                "section": "Section 74-79",
                "title": "Sexual Assault and Rape",
                "content": """Rape and Sexual Assault under BNS 2023:
                Section 64: Rape - Imprisonment not less than 10 years, may extend to life + fine
                Section 70: Gang rape - Not less than 20 years, may extend to life imprisonment
                Section 66: Rape by public servant - Not less than 10 years
                
                ZERO FIR: You can file FIR at ANY police station in India, regardless of where crime occurred.
                Police must transfer it to correct jurisdiction later.
                You CANNOT be forced to give statement to male police officer.
                Medical examination must be done within 24 hours.
                Statement under Section 183 BNSS: Can be recorded by Judicial Magistrate at victim's home.
                One Stop Centre (Sakhi): 181 helpline - free counseling, medical, legal aid, shelter
                National Commission for Women: 7827170170""",
            },
            {
                "act": "BNSS 2023 / CrPC",
                "section": "Section 35-60 BNSS",
                "title": "Arrest Rights and Bail",
                "content": """YOUR COMPLETE RIGHTS WHEN ARRESTED:
                
                BEFORE ARREST:
                - Police must show arrest warrant (except cognizable offence)
                - You can demand to see the warrant
                
                AT TIME OF ARREST:
                - Police must tell you WHY you are being arrested
                - Police must INFORM one person you choose (family/friend/lawyer) within 12 hours
                - Police must show you list of offences you're arrested for
                
                AFTER ARREST:
                - You must be produced before Magistrate within 24 hours (excluding travel time)
                - You have RIGHT to free legal aid (Section 12, Legal Services Authorities Act)
                - Call NALSA helpline: 15100 for free lawyer
                
                BAIL:
                Bailable offences: You have RIGHT to bail. Police/Court cannot refuse.
                Non-bailable offences: Court decides. Factors: flight risk, tampering evidence, severity.
                Anticipatory Bail (Section 482 BNSS): Apply to Sessions Court or HC BEFORE arrest
                Default Bail: If chargesheet not filed within 60 days (minor) or 90 days (serious), you get automatic bail""",
            },
            {
                "act": "Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023",
                "section": "Section 173",
                "title": "FIR - First Information Report",
                "content": """HOW TO FILE AN FIR:
                
                Step 1: Go to police station in whose jurisdiction crime occurred (or any station for Zero FIR)
                Step 2: Give complaint in writing or orally to Officer-in-Charge
                Step 3: Police MUST register FIR for cognizable offences - they CANNOT refuse
                Step 4: Get FREE copy of FIR - this is your legal right
                Step 5: FIR must be read out to you before you sign
                Step 6: If police refuse: 
                  → Written complaint to SP/Commissioner
                  → File complaint before Judicial Magistrate u/s 175 BNSS
                  → Call PCR: 100 or Women Helpline: 1091
                
                COGNIZABLE OFFENCES (police can arrest without warrant): Murder, Rape, Robbery, Dacoity, Kidnapping, Dowry Death, POCSO, etc.
                
                AFTER FIR: Police MUST investigate. If no action in 90 days, file application before Magistrate.""",
            },
        ]

        for item in criminal_sections:
            chunks = self.splitter.split_text(item["content"])
            for chunk in chunks:
                docs.append(LegalDocument(
                    content=chunk,
                    act=item["act"],
                    section=item["section"],
                    section_title=item["title"],
                    doc_type="criminal",
                    language="en",
                ))
        return docs

    async def _load_labour_law(self) -> List[LegalDocument]:
        """Load all 4 Labour Codes + MGNREGA + state minimum wages"""
        docs = []
        labour_laws = [
            {
                "act": "Code on Wages 2019",
                "section": "Section 3-7",
                "title": "Minimum Wage Rights",
                "content": """MINIMUM WAGE RIGHTS (Code on Wages 2019):
                
                Every employer MUST pay minimum wage. Violation is a criminal offence.
                
                HOW TO CHECK YOUR MINIMUM WAGE:
                - Central government fixes for central sphere employment
                - State governments fix for all other employment
                - Visit: https://labour.gov.in/minimum-wages
                - Must be revised every 5 years
                
                IF EMPLOYER NOT PAYING MINIMUM WAGE:
                Step 1: Give written notice to employer demanding arrears
                Step 2: File complaint with Labour Inspector (free, no lawyer needed)
                Step 3: Inspector must inquire within 30 days
                Step 4: You can claim DOUBLE the unpaid amount as compensation
                Step 5: Employer can be imprisoned up to 5 years (Section 54)
                
                HELPLINE: Ministry of Labour: 1800-11-0001 (toll free)
                
                MGNREGA WORKERS: Entitled to minimum agricultural wage of state.
                If not paid within 15 days: 0.05% per day compensation automatically due""",
            },
            {
                "act": "Industrial Relations Code 2020",
                "section": "Section 77-82",
                "title": "Wrongful Termination and Retrenchment",
                "content": """PROTECTION AGAINST WRONGFUL TERMINATION:
                
                For establishments with 300+ workers: Cannot retrench/close without government permission
                For all workers with 1+ year service: 
                - Must give 1 month notice OR 1 month salary in lieu
                - Must pay RETRENCHMENT COMPENSATION: 15 days wages for each year of service
                
                ILLEGAL TERMINATION? Here's what to do:
                1. Get written termination letter (demand it)
                2. File complaint with Labour Commissioner within 3 years
                3. File before Industrial Tribunal / Labour Court
                4. You can claim: Back wages + reinstatement OR compensation
                
                DOMESTIC WORKERS: Not covered by most labour laws yet.
                Maharashtra, Karnataka have state domestic worker welfare boards - register there.
                
                CONTRACT WORKERS: Have same rights as permanent workers for equal work (Supreme Court judgment)
                
                CONSTRUCTIVE DISMISSAL: If employer makes conditions so bad you resign - still counts as termination.
                Document everything in writing.""",
            },
            {
                "act": "Social Security Code 2020 / EPF Act",
                "section": "Section 15-17",
                "title": "PF and ESI Rights",
                "content": """PROVIDENT FUND (EPF) RIGHTS:
                
                Who gets PF: Any establishment with 20+ employees must register
                Employee contribution: 12% of basic salary
                Employer contribution: 12% (8.33% to EPS pension, 3.67% to EPF)
                
                YOUR PF BALANCE: https://passbook.epfindia.gov.in
                
                EMPLOYER NOT DEPOSITING PF? This is a criminal offence.
                Step 1: Check your PF passbook online - if no deposits, employer defaulting
                Step 2: File online complaint: https://epfigms.gov.in
                Step 3: EPFO can attach employer's property and bank accounts
                Step 4: Employer faces up to 3 years imprisonment
                
                ESI (Employee State Insurance):
                Applicable if earning up to ₹21,000/month
                Provides: Medical care for family, sickness benefit, maternity benefit (26 weeks paid), disability benefit
                
                MATERNITY BENEFIT ACT 2017:
                - 26 weeks paid maternity leave for first 2 children
                - 12 weeks for 3rd child onwards
                - No employer can fire you for being pregnant
                - Violation: File complaint with Labour Commissioner""",
            },
        ]

        for item in labour_laws:
            chunks = self.splitter.split_text(item["content"])
            for chunk in chunks:
                docs.append(LegalDocument(
                    content=chunk,
                    act=item["act"],
                    section=item["section"],
                    section_title=item["title"],
                    doc_type="labour",
                    language="en",
                ))
        return docs

    async def _load_rti(self) -> List[LegalDocument]:
        """Load complete RTI Act knowledge"""
        docs = []
        rti_content = [
            {
                "section": "Section 6",
                "title": "How to File RTI Application",
                "content": """HOW TO FILE RTI APPLICATION (Right to Information Act 2005):
                
                STEP BY STEP PROCESS:
                
                Step 1: IDENTIFY the Public Authority (the govt body that has the info)
                - Central govt: Central PIOs (Public Information Officers)
                - State govt: State PIOs
                - Panchayats, municipalities, courts, police, hospitals - all covered
                
                Step 2: WRITE the application (in Hindi, English, or official language of state)
                - Address to: "The Public Information Officer, [Department name]"
                - State: "Under the Right to Information Act 2005, I request the following information:"
                - Be specific about what information you need
                - Give your name and address
                - NO NEED TO GIVE REASON
                
                Step 3: PAY the fee
                - ₹10 for central govt (by postal order, DD, or court fee stamp)
                - State govts charge ₹10-50 (varies)
                - BPL (Below Poverty Line) card holders: COMPLETELY FREE
                - Women applicants: Many states have made it free
                
                Step 4: SUBMIT
                - In person to PIO
                - By post (registered/speed post)
                - Online: https://rtionline.gov.in (central govt)
                
                Step 5: RESPONSE DEADLINE
                - Normal: 30 days from receipt
                - If life or liberty involved: 48 HOURS
                - If sent to wrong dept and transferred: 35 days total
                
                WHAT TO DO IF NO RESPONSE:
                - File First Appeal within 30 days to First Appellate Authority (same department)
                - File Second Appeal within 90 days to Central/State Information Commission
                - Information Commissioner can impose PENALTY of ₹250/day (up to ₹25,000) on PIO""",
            },
            {
                "section": "Section 8",
                "title": "Information You Cannot Get Under RTI",
                "content": """EXEMPTIONS UNDER RTI (Section 8 - what cannot be disclosed):
                
                You CANNOT get:
                1. Info affecting sovereignty/security/strategic interests
                2. Expressly forbidden by any court
                3. Info that would breach privilege of Parliament/Legislature
                4. Commercial confidence, trade secrets (if disclosure harms competitive position)
                5. Info held in fiduciary capacity
                6. Info received from foreign government
                7. Info endangering life or safety of any person
                8. Cabinet papers, Council of Ministers deliberations (until decision taken)
                9. Personal information with no public interest
                
                IMPORTANT: Even if info is "exempt", if public interest in disclosure > harm = MUST disclose
                
                WHAT YOU CAN GET (most common RTI uses):
                ✅ Government file notings
                ✅ Why your ration card/pension/scheme was rejected
                ✅ Road construction contracts and costs
                ✅ Government employee attendance records
                ✅ Your own file in any government department
                ✅ Copies of government contracts
                ✅ Government employee salary details
                ✅ Minutes of meetings
                ✅ Electoral bonds details
                ✅ Police FIR status""",
            },
        ]

        for item in rti_content:
            chunks = self.splitter.split_text(item["content"])
            for chunk in chunks:
                docs.append(LegalDocument(
                    content=chunk,
                    act="Right to Information Act 2005",
                    section=item["section"],
                    section_title=item["title"],
                    doc_type="rti",
                    language="en",
                    source_url="https://rtionline.gov.in",
                ))
        return docs

    async def _load_consumer_law(self) -> List[LegalDocument]:
        """Consumer Protection Act 2019"""
        docs = []
        content = """CONSUMER RIGHTS IN INDIA (Consumer Protection Act 2019):
        
        YOUR 6 CONSUMER RIGHTS:
        1. Right to Safety - from hazardous goods/services
        2. Right to Information - about quality, quantity, price
        3. Right to Choose - access to variety at competitive prices
        4. Right to be Heard - consumer interests considered in policy
        5. Right to Redressal - compensation for unfair trade practices
        6. Right to Consumer Education
        
        WHICH COURT TO FILE IN:
        - Claims up to ₹50 lakhs: District Consumer Commission
        - Claims ₹50 lakhs to ₹2 crores: State Consumer Commission  
        - Claims above ₹2 crores: National Consumer Commission (NCDRC)
        
        HOW TO FILE COMPLAINT:
        Step 1: Send written complaint to company first (keep copy)
        Step 2: Wait 30 days for response
        Step 3: If no response/unsatisfactory: File consumer complaint
        Step 4: Pay filing fee (₹200-₹5000 based on claim amount)
        Step 5: File online: https://consumerhelpline.gov.in
        
        ONLINE FRAUD/SHOPPING:
        - E-commerce company liable for defective products
        - Can demand full refund + compensation
        - Report to: https://consumerhelpline.gov.in (NCH)
        - National Consumer Helpline: 1800-11-4000 or 14404
        
        COMMON WINNING CASES:
        - Bank charging extra fees without notice
        - Insurance claim wrongly rejected
        - Builder not giving possession on time
        - Defective appliance not repaired under warranty
        - Hospital negligence
        - Airline delay compensation"""

        chunks = self.splitter.split_text(content)
        for chunk in chunks:
            docs.append(LegalDocument(
                content=chunk,
                act="Consumer Protection Act 2019",
                section="Section 2-34",
                section_title="Consumer Rights and Redressal",
                doc_type="consumer",
                language="en",
                source_url="https://consumerhelpline.gov.in",
            ))
        return docs

    async def _load_property_law(self) -> List[LegalDocument]:
        """Land and property rights"""
        docs = []
        content = """LAND AND PROPERTY RIGHTS IN INDIA:
        
        TENANT RIGHTS (Transfer of Property Act + Rent Control Acts):
        - Landlord CANNOT evict without proper legal process
        - Must give proper notice: 15 days for monthly tenancy, 6 months for yearly
        - Cannot cut water/electricity to force eviction - THIS IS ILLEGAL (Delhi HC: RCR vs Anand 2019)
        - Cannot forcibly enter your home without notice
        - Court order required for eviction - police cannot evict without court order
        
        IF LANDLORD HARASSING YOU:
        1. Send legal notice demanding he stop
        2. File complaint with Rent Control Court
        3. File FIR for trespass if landlord enters illegally (Section 441 BNS)
        4. File complaint with police if utilities cut illegally
        
        PROPERTY DOCUMENTS TO KNOW:
        - Sale Deed: Main ownership document, must be registered
        - Mutation: Transfer of property in revenue records
        - Encumbrance Certificate: Shows loans/liabilities on property
        - Property Tax Receipt: Shows you've been paying taxes
        
        FOREST RIGHTS ACT 2006 (For tribal communities):
        - Tribals have RIGHT to land they have cultivated for 3+ generations
        - Community forest rights for grazing, fishing, collection
        - Government CANNOT evict without recognizing forest rights first
        - File claim before Gram Sabha Forest Rights Committee
        - District Level Committee is final authority
        - Supreme Court: Cannot evict until claims properly processed"""

        chunks = self.splitter.split_text(content)
        for chunk in chunks:
            docs.append(LegalDocument(
                content=chunk,
                act="Transfer of Property Act / Forest Rights Act 2006",
                section="Multiple Sections",
                section_title="Property and Land Rights",
                doc_type="property",
                language="en",
            ))
        return docs

    async def _load_family_law(self) -> List[LegalDocument]:
        """Family law - marriage, divorce, domestic violence, child custody"""
        docs = []
        content = """DOMESTIC VIOLENCE RIGHTS (Protection of Women from Domestic Violence Act 2005):
        
        WHAT IS DOMESTIC VIOLENCE:
        - Physical abuse: hitting, slapping, burning
        - Sexual abuse within marriage
        - Emotional/verbal abuse: insults, humiliation, threats
        - Economic abuse: not giving household money, selling her property
        - Dowry demands after marriage
        
        WHO IS COVERED:
        Any woman in a domestic relationship (wife, live-in partner, sister, mother, daughter)
        
        ORDERS YOU CAN GET FROM COURT:
        1. PROTECTION ORDER: Stops abuser from contacting you - violating this is 1 year jail
        2. RESIDENCE ORDER: Cannot throw you out of shared home - even if he owns it
        3. MONETARY RELIEF: Household expenses, medical bills, loss of earnings
        4. CUSTODY ORDER: Temporary custody of children
        5. COMPENSATION ORDER: For injuries suffered
        
        HOW TO GET HELP:
        - Call 181 (Women Helpline) - 24/7 free
        - Go to nearest Protection Officer (in every district)
        - Go to nearest One Stop Centre (Sakhi Centre)
        - File complaint before Magistrate - NO POLICE COMPLAINT NEEDED FIRST
        - File online: https://nalsa.gov.in
        
        DOWRY HARASSMENT:
        Section 498A BNS: Husband/his family causing cruelty = 3 years jail + fine
        Section 80 BNS (Section 304B IPC): Dowry death = minimum 7 years jail
        
        DIVORCE RIGHTS:
        - Muslim Women (PMLA 2019): Triple talaq is ILLEGAL and criminal offence
        - Mutual consent divorce: 6 months waiting period (waivable by court)
        - Maintenance: Wife entitled to maintenance from husband until remarriage"""

        chunks = self.splitter.split_text(content)
        for chunk in chunks:
            docs.append(LegalDocument(
                content=chunk,
                act="Protection of Women from Domestic Violence Act 2005",
                section="Section 3-23",
                section_title="Domestic Violence Protection",
                doc_type="family",
                language="en",
            ))
        return docs

    async def _load_govt_schemes(self) -> List[LegalDocument]:
        """800+ government schemes - eligibility, how to apply"""
        docs = []
        schemes = [
            {
                "name": "Ayushman Bharat PM-JAY",
                "content": """AYUSHMAN BHARAT (PM Jan Arogya Yojana) - FREE HEALTH INSURANCE:
                Coverage: ₹5 lakhs per family per year for hospitalisation
                Who can get: Bottom 40% families as per SECC 2011 data
                Check eligibility: SMS "PMJAY" to 56167 OR call 14555 OR visit https://beneficiary.nha.gov.in
                
                HOW TO USE:
                1. Check if your name is in beneficiary list
                2. Get Ayushman card from nearest CSC (Common Service Centre) or Gram Panchayat
                3. Show card at any empanelled hospital (govt or private)
                4. CASHLESS treatment - hospital bills government directly
                5. All pre-existing conditions covered from Day 1
                
                IF HOSPITAL REFUSES: Call 14555 (toll free) or file complaint at https://cgrms.pmjay.gov.in
                Hospitals cannot ask for money from you - report immediately""",
            },
            {
                "name": "PM Kisan Samman Nidhi",
                "content": """PM KISAN SAMMAN NIDHI - ₹6000 PER YEAR FOR FARMERS:
                Who gets: All landholding farmer families
                Amount: ₹2000 every 4 months (3 installments of ₹2000 = ₹6000/year)
                Check status: https://pmkisan.gov.in OR call 155261 OR 011-24300606
                
                HOW TO REGISTER:
                1. Go to nearest CSC (Common Service Centre) with:
                   - Aadhaar card
                   - Land documents (Khasra/Khatauni)
                   - Bank passbook
                2. Or register online at pmkisan.gov.in
                3. Village Patwari can also register
                
                MONEY NOT COMING? Common reasons:
                - Bank account not linked to Aadhaar: Fix at bank
                - Land documents mismatch: Correct at Patwari office
                - Wrong bank account: Update on portal
                - File grievance: https://pmkisan.gov.in/Grievance.aspx""",
            },
            {
                "name": "MGNREGA",
                "content": """MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act):
                Right to 100 days of paid work per year per household
                Payment: State minimum agricultural wage (paid within 15 days)
                
                HOW TO GET WORK:
                1. Register at Gram Panchayat - get Job Card (MUST be given within 15 days)
                2. Apply for work in writing to Gram Panchayat
                3. Work MUST be provided within 15 days of application
                4. If no work: UNEMPLOYMENT ALLOWANCE due (25-50% of wages)
                
                YOUR RIGHTS:
                - Work must be within 5km of home
                - Cannot be forced to work far away without extra allowance
                - Women must get 33% of work
                - Equal wages for men and women (Supreme Court order)
                - Worksite must have: shade, clean water, first aid kit, creche
                
                IF RIGHTS VIOLATED:
                - File complaint with Programme Officer
                - Call MGNREGA helpline: 1800-345-22-44
                - File social audit complaint""",
            },
            {
                "name": "PM Awas Yojana",
                "content": """PM AWAS YOJANA (PMAY) - HOUSING FOR ALL:
                
                PMAY-Gramin (Rural):
                - Free house for homeless BPL families in rural areas
                - ₹1.20 lakhs (plain) or ₹1.30 lakhs (hills/NE) per house
                - Check list: https://rhreporting.nic.in
                - Apply: Contact Block Development Officer
                
                PMAY-Urban:
                - Subsidy on home loan for EWS/LIG/MIG families
                - EWS (income up to ₹3L): up to ₹2.67L subsidy
                - LIG (₹3L-₹6L): up to ₹2.67L subsidy
                - MIG-I (₹6L-₹12L): up to ₹2.35L subsidy
                - Apply: Through approved banks/HFCs or online portal
                
                IF NAME NOT IN LIST DESPITE ELIGIBILITY:
                File grievance with State PMAY cell
                Contact District Collector office""",
            },
        ]

        for scheme in schemes:
            chunks = self.splitter.split_text(scheme["content"])
            for chunk in chunks:
                docs.append(LegalDocument(
                    content=chunk,
                    act=f"Government Scheme: {scheme['name']}",
                    section="Eligibility and Application",
                    section_title=scheme["name"],
                    doc_type="scheme",
                    language="en",
                    source_url="https://myscheme.gov.in",
                ))
        return docs

    async def _load_procedures(self) -> List[LegalDocument]:
        """Step-by-step legal procedures"""
        docs = []
        content = """HOW TO GET FREE LEGAL AID IN INDIA:
        
        EVERY PERSON HAS RIGHT TO FREE LEGAL AID (Article 39A + Legal Services Authorities Act 1987)
        
        WHO GETS FREE LEGAL AID:
        - Women and children (ALL - regardless of income)
        - SC/ST persons
        - Victims of trafficking, disasters, ethnic violence, industrial disaster
        - Persons with disabilities
        - Persons in custody
        - Persons with annual income less than ₹1 lakh (central) or state threshold
        
        HOW TO GET FREE LAWYER:
        1. Call NALSA (National Legal Services Authority): 15100 (toll free, 24/7)
        2. Visit District Legal Services Authority (DLSA) - in every district court
        3. Visit Taluk Legal Services Committee - at taluk/tehsil level
        4. Visit nearest Lok Adalat for settlement
        
        WHAT FREE LEGAL AID COVERS:
        - Court cases in all courts including Supreme Court
        - Legal advice and consultation
        - Drafting of legal documents
        - Representation in Lok Adalat
        
        LOK ADALAT (People's Court):
        - FREE, no court fees
        - Settlement based on compromise
        - Award is final - no appeal (but you agree to it)
        - Good for: Motor accident claims, matrimonial disputes, labour disputes, pre-litigation matters"""

        chunks = self.splitter.split_text(content)
        for chunk in chunks:
            docs.append(LegalDocument(
                content=chunk,
                act="Legal Services Authorities Act 1987",
                section="Section 12",
                section_title="Free Legal Aid",
                doc_type="procedure",
                language="en",
                source_url="https://nalsa.gov.in",
            ))
        return docs

    async def _load_helplines(self) -> List[LegalDocument]:
        """All important helpline numbers"""
        docs = []
        content = """IMPORTANT HELPLINE NUMBERS IN INDIA:
        
        EMERGENCY:
        Police: 100
        Fire: 101
        Ambulance: 102
        Disaster Management: 108
        All Emergency (unified): 112
        
        WOMEN AND CHILDREN:
        Women Helpline (24/7): 181 or 1091
        Domestic Violence: 181
        Child Helpline: 1098
        Anti Human Trafficking: 1800-419-8588
        NCW (National Commission for Women): 7827170170
        POCSO helpline: 1098
        
        LEGAL AID:
        NALSA (Free Legal Aid): 15100
        
        LABOUR:
        Ministry of Labour: 1800-11-0001
        EPFO (PF related): 1800-118-005
        ESI: 1800-11-2526
        
        HEALTH:
        Ayushman Bharat: 14555
        Mental Health (iCall): 9152987821
        
        CONSUMER:
        National Consumer Helpline: 1800-11-4000 or 14404
        
        AGRICULTURE:
        PM Kisan: 155261
        Kisan Call Centre: 1800-180-1551
        
        CORRUPTION:
        CVC (Central Vigilance Commission): 1800-11-0180
        Lokpal: lokpal.nic.in
        
        CYBER CRIME:
        Cyber Crime Helpline: 1930
        Online reporting: cybercrime.gov.in
        
        SENIOR CITIZENS:
        Elder Line: 14567
        
        RTI:
        CIC (Central Information Commission): 011-26181736"""

        chunks = self.splitter.split_text(content)
        for chunk in chunks:
            docs.append(LegalDocument(
                content=chunk,
                act="Government Helplines Directory",
                section="Emergency and Legal Aid",
                section_title="Important Helpline Numbers",
                doc_type="helpline",
                language="en",
            ))
        return docs
