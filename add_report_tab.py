"""
Prune startups.json to 2020+ founded companies, regenerate the map,
then inject a sortable/filterable Report tab into the HTML.
"""
import json, re, sys
sys.path.insert(0, '.')
import map_gen

# ── Founding years ─────────────────────────────────────────────────────────────
FOUNDED = {
    "Airbnb": 2008, "DoorDash": 2013, "Coinbase": 2012, "Groww": 2016,
    "Oklo": 2013, "Instacart": 2012, "Meesho": 2015, "EquipmentShare": 2015,
    "Dropbox": 2007, "Rigetti Computing": 2013, "GitLab": 2011,
    "BillionToOne": 2016, "Matterport": 2011, "Amplitude": 2012,
    "PagerDuty": 2009, "Ginkgo Bioworks": 2009, "Weave": 2015,
    "Pardes Biosciences": 2020, "Embark Trucks": 2016, "Lucira Health": 2013,
    "Momentus": 2017, "Segment": 2011, "Algolia": 2012, "Truebill": 2015,
    "Twitch": 2011, "PlanGrid": 2011, "Bellabeat": 2013, "Cruise": 2013,
    "Benchling": 2012, "Casetext": 2013, "Bird": 2017, "Brex": 2017,
    "The Athletic": 2016, "Codecademy": 2011, "Checkr": 2014, "Lever": 2012,
    "Clipboard Health": 2016, "Heap": 2013, "Sendwave": 2014, "Deel": 2019,
    "Clever": 2012, "Caper": 2016, "Reddit": 2005, "Fivestars": 2011,
    "Machine Zone": 2008, "Faire": 2017, "Fivetran": 2012, "Optimizely": 2009,
    "Flexport": 2013, "WePay": 2008, "Weebly": 2006, "Flock Safety": 2017,
    "Sqreen": 2015, "NURX": 2015, "Go1": 2015, "CoreOS": 2013,
    "Bear Flag Robotics": 2017, "GOAT Group": 2015, "Heroku": 2007,
    "GrubMarket": 2015, "HelloSign": 2010, "Zenefits": 2013, "Gusto": 2012,
    "Honeylove": 2018, "Modern Fertility": 2017, "Cognito": 2014,
    "OpenInvest": 2015, "Mixpanel": 2009, "Paystack": 2016,
    "Moxion Power Co.": 2020, "DrChrono": 2009, "OMGPop": 2006,
    "Newfront": 2017, "North": 2012, "Nowports": 2018, "Odeko": 2019,
    "GitPrime": 2015, "Proxy": 2016, "FutureAdvisor": 2010, "Podium": 2014,
    "Rappi": 2015, "Razorpay": 2014, "Rippling": 2016, "Scale AI": 2016,
    "Scentbird": 2014, "Scribd": 2007, "ShipBob": 2014, "SmartAsset": 2012,
    "Stripe": 2010, "Wave": 2017, "Webflow": 2013, "Whatnot": 2019,
    "Zapier": 2011, "Zepto": 2021, "Focal Systems": 2015, "Mio": 2015,
    "Daily": 2016, "Petcube": 2012, "Outschool": 2015, "Mason": 2018,
    "MagicBus": 2015, "Tovala": 2015, "iSono Health": 2015, "GetAccept": 2017,
    "Chatfuel": 2015, "Yardbook": 2014, "GoCardless": 2011,
    "Stealth Worker": None, "Deepgram": 2015, "SOUNDBOKS": 2015,
    "Lattice": 2015, "Mux": 2017, "Human Interest": 2015, "Flirtey (SkyDrop)": 2013,
    "Eight Sleep": 2014, "Instawork": 2015, "Cofactor Genomics": 2014,
    "Click & Grow": 2010, "Bitmovin": 2012, "TetraScience": 2016,
    "The Ticket Fairy": 2012, "Font Awesome": 2012, "80,000 Hours": 2011,
    "Xendit": 2015, "Shred Video": 2015, "Shape (ShapeScale)": 2016,
    "RedCarpetUp": 2012, "Plate IQ": 2015, "PickTrace": 2016, "Fountain": 2014,
    "Microhealth": 2014, "Zeplin": 2015, "Markhor": 2013, "Circle Medical": 2015,
    "GiveCampus": 2014, "Drip Capital": 2016, "Chaldal": 2013, "Clerky": 2011,
    "Bodyport": 2017, "Verge Genomics": 2015, "Thrive Agritech": 2015,
    "Tesorio": 2015, "AgileMD": 2013, "Reach": 2016, "SunFarmer": 2013,
    "Confident LIMS": 2016, "Branch8": 2017, "Heroic Labs": 2014,
    "SnapMagic": 2013, "Scope AR": 2011, "PartnerStack": 2015, "Assembly": 2020,
    "Gemnote": 2015, "New Story": 2015, "Ironclad": 2017,
    "Leaders In Tech": 2017, "teaBOT": 2016, "Teleport": 2015, "Lugg": 2015,
    "Shasqi": 2014, "Adyen": 2006, "BAE Systems, Inc.": 1999,
    "GameChanger": 2009, "MassMutual": 1851, "Teachable": 2013,
    "Riskified": 2012, "GlossGenius": 2016, "Dandy": 2020, "Upstart": 2012,
    "Radar": 2016, "Chime": 2013, "Smartling": 2009, "Current": 2015,
    "Superblocks": 2020, "Collectors": 2017, "Granted": 2021,
    "Spot & Tango": 2018, "Findigs, Inc.": 2019, "Squarespace": 2003,
    "firsthand Health Inc": 2021,
}

# ── Funding data: (display, amount_millions, status, notes) ────────────────────
FUNDING = {
    "Airbnb": ("~$6B", 6000, "Public", "NASDAQ: ABNB · IPO Dec 2020"),
    "DoorDash": ("~$2.5B", 2500, "Public", "NYSE: DASH · IPO Dec 2020"),
    "Coinbase": ("~$547M", 547, "Public", "NASDAQ: COIN · Direct listing Apr 2021"),
    "Groww": ("~$1.6B", 1600, "Private", "Valued ~$3B · India"),
    "Oklo": ("~$100M+", 100, "Public", "NYSE: OKLO · SPAC May 2024"),
    "Instacart": ("~$2.9B", 2900, "Public", "NASDAQ: CART · IPO Sept 2023"),
    "Meesho": ("~$1.1B", 1100, "Private", "Valued ~$3.9B · India"),
    "EquipmentShare": ("~$2B+", 2000, "Private", "Valued $3.3B+"),
    "Dropbox": ("~$1.7B", 1700, "Public", "NASDAQ: DBX · IPO Mar 2018"),
    "Rigetti Computing": ("~$200M", 200, "Public", "NASDAQ: RGTI · SPAC 2022"),
    "GitLab": ("~$1.4B", 1400, "Public", "NASDAQ: GTLB · IPO Oct 2021"),
    "BillionToOne": ("~$364M", 364, "Private", "Unicorn as of 2023"),
    "Matterport": ("~$352M", 352, "Acquired", "SPAC 2021 · Acquired by CoStar 2024 for ~$1.6B"),
    "Amplitude": ("~$336M", 336, "Public", "NASDAQ: AMPL · IPO Sept 2021"),
    "PagerDuty": ("~$173M", 173, "Public", "NYSE: PD · IPO Apr 2019"),
    "Ginkgo Bioworks": ("~$1.7B", 1700, "Public", "NYSE: DNA · SPAC 2021"),
    "Weave": ("~$253M", 253, "Public", "NYSE: WEAV · IPO Nov 2021"),
    "Pardes Biosciences": ("~$144M", 144, "Defunct", "SPAC Jan 2022 · wound down 2023"),
    "Embark Trucks": ("~$317M", 317, "Defunct", "SPAC 2021 · ceased operations Mar 2023"),
    "Lucira Health": ("~$235M", 235, "Acquired", "Bankruptcy Feb 2023 · Acquired by Pfizer for ~$25M"),
    "Momentus": ("~$170M", 170, "Public", "NASDAQ: MNTS · SPAC 2021"),
    "Segment": ("~$284M", 284, "Acquired", "Acquired by Twilio 2020 for $3.2B"),
    "Algolia": ("~$335M", 335, "Private", ""),
    "Truebill": ("~$148M", 148, "Acquired", "Acquired by Rocket Companies Dec 2021 for $1.275B"),
    "Twitch": ("~$35M", 35, "Acquired", "Acquired by Amazon Aug 2014 for ~$970M"),
    "PlanGrid": ("~$131M", 131, "Acquired", "Acquired by Autodesk Dec 2018 for $875M"),
    "Bellabeat": ("~$60M", 60, "Private", ""),
    "Cruise": ("~$10B+", 10000, "Subsidiary", "GM + SoftBank + Honda + others"),
    "Benchling": ("~$690M", 690, "Private", "Valued ~$6.1B (2021)"),
    "Casetext": ("~$65M", 65, "Acquired", "Acquired by Thomson Reuters Aug 2023 for $650M"),
    "Bird": ("~$776M", 776, "Defunct", "SPAC 2022 · filed bankruptcy Dec 2023"),
    "Brex": ("~$1.5B", 1500, "Private", "Valued $12.3B (2022)"),
    "The Athletic": ("~$139M", 139, "Acquired", "Acquired by NY Times Feb 2022 for $550M"),
    "Codecademy": ("~$82.6M", 82.6, "Acquired", "Acquired by Skillsoft 2022 for $525M"),
    "Checkr": ("~$679M", 679, "Private", "Valued $5B (2022)"),
    "Lever": ("~$73M", 73, "Acquired", "Acquired by Employ Inc. 2022"),
    "Clipboard Health": ("~$80M", 80, "Private", ""),
    "Heap": ("~$205M", 205, "Acquired", "Acquired by Contentsquare 2023"),
    "Sendwave": ("~$11M", 11, "Acquired", "Acquired by WorldRemit 2020 for ~$500M"),
    "Deel": ("~$679M", 679, "Private", "Valued $12B (2022)"),
    "Clever": ("~$56M", 56, "Private", ""),
    "Caper": ("~$20M", 20, "Acquired", "Acquired by Instacart 2021 for ~$350M"),
    "Reddit": ("~$1.3B", 1300, "Public", "NYSE: RDDT · IPO Mar 2024"),
    "Fivestars": ("~$105.5M", 105.5, "Acquired", "Acquired by SumUp 2021"),
    "Machine Zone": ("~$616M", 616, "Acquired", "Assets sold to AppLovin 2020 for ~$600M"),
    "Faire": ("~$1.4B", 1400, "Private", "Valued $12.4B (2022)"),
    "Fivetran": ("~$730M", 730, "Private", "Valued $5.6B (2021)"),
    "Optimizely": ("~$251M", 251, "Acquired", "Acquired by Episerver 2020"),
    "Flexport": ("~$2.3B", 2300, "Private", "Valued $8B (2022)"),
    "WePay": ("~$75M", 75, "Acquired", "Acquired by JPMorgan Chase 2017"),
    "Weebly": ("~$35.7M", 35.7, "Acquired", "Acquired by Square (Block) 2018 for $365M"),
    "Flock Safety": ("~$380M", 380, "Private", "Valued $3.5B (2022)"),
    "Sqreen": ("~$14.3M", 14.3, "Acquired", "Acquired by Datadog Feb 2021"),
    "NURX": ("~$92M", 92, "Private", ""),
    "Go1": ("~$400M", 400, "Private", "Valued $2B (2022)"),
    "CoreOS": ("~$48M", 48, "Acquired", "Acquired by Red Hat 2018 for ~$250M"),
    "Bear Flag Robotics": ("~$23.8M", 23.8, "Acquired", "Acquired by John Deere 2021 for $250M"),
    "GOAT Group": ("~$595M", 595, "Private", "Valued $3.7B (2021)"),
    "Heroku": ("~$13M", 13, "Acquired", "Acquired by Salesforce 2011 for $212M"),
    "GrubMarket": ("~$604M", 604, "Private", "Valued $3.5B (2022)"),
    "HelloSign": ("~$16M", 16, "Acquired", "Acquired by Dropbox 2019 for $230M"),
    "Zenefits": ("~$583M", 583, "Private", ""),
    "Gusto": ("~$750M", 750, "Private", ""),
    "Honeylove": ("~$2M", 2, "Private", "Largely bootstrapped"),
    "Modern Fertility": ("~$22M", 22, "Acquired", "Acquired by Ro 2021 for $225M"),
    "Cognito": ("~$10M", 10, "Private", ""),
    "OpenInvest": ("~$10.4M", 10.4, "Acquired", "Acquired by JPMorgan 2021"),
    "Mixpanel": ("~$77M", 77, "Private", ""),
    "Paystack": ("~$10M", 10, "Acquired", "Acquired by Stripe 2020 for $200M+"),
    "Moxion Power Co.": ("~$130M", 130, "Private", ""),
    "DrChrono": ("~$30M", 30, "Acquired", "Acquired by EverCommerce 2022"),
    "OMGPop": ("~$16.5M", 16.5, "Acquired", "Acquired by Zynga 2012 for $183M"),
    "Newfront": ("~$315M", 315, "Private", ""),
    "North": ("~$135M", 135, "Acquired", "Acquired by Google 2020 for ~$180M"),
    "Nowports": ("~$150M", 150, "Private", ""),
    "Odeko": ("~$190M", 190, "Private", ""),
    "GitPrime": ("~$17M", 17, "Acquired", "Acquired by Pluralsight 2019"),
    "Proxy": ("~$45M", 45, "Private", ""),
    "FutureAdvisor": ("~$21M", 21, "Acquired", "Acquired by BlackRock 2015"),
    "Podium": ("~$601M", 601, "Private", ""),
    "Rappi": ("~$2B", 2000, "Private", "Latin America super-app"),
    "Razorpay": ("~$740M", 740, "Private", "Valued $7.5B (2021) · India"),
    "Rippling": ("~$1.2B", 1200, "Private", ""),
    "Scale AI": ("~$1.6B", 1600, "Private", "Valued $13.8B (2024)"),
    "Scentbird": ("~$10M", 10, "Private", ""),
    "Scribd": ("~$105M", 105, "Private", ""),
    "ShipBob": ("~$330M", 330, "Private", ""),
    "SmartAsset": ("~$161M", 161, "Private", ""),
    "Stripe": ("~$8.7B", 8700, "Private", "Valued $65B (2023)"),
    "Wave": ("~$200M", 200, "Private", "Mobile money for Africa"),
    "Webflow": ("~$330M", 330, "Private", ""),
    "Whatnot": ("~$685M", 685, "Private", "Valued $3.7B (2022)"),
    "Zapier": ("~$1.4B", 1400, "Private", ""),
    "Zepto": ("~$900M", 900, "Private", "Quick commerce · India"),
    "Focal Systems": ("~$30M", 30, "Private", ""),
    "Mio": ("~$25M", 25, "Private", ""),
    "Daily": ("~$36M", 36, "Private", "Video API"),
    "Petcube": ("~$15M", 15, "Private", ""),
    "Outschool": ("~$130M", 130, "Private", ""),
    "Mason": ("~$6M", 6, "Private", ""),
    "MagicBus": ("~$28M", 28, "Private", "India education"),
    "Tovala": ("~$60M", 60, "Private", ""),
    "iSono Health": ("~$12M", 12, "Private", ""),
    "GetAccept": ("~$61M", 61, "Private", ""),
    "Chatfuel": ("~$7M", 7, "Private", ""),
    "Yardbook": ("Unknown", None, "Private", "Largely bootstrapped"),
    "GoCardless": ("~$800M+", 800, "Private", ""),
    "Stealth Worker": ("Unknown", None, "Unknown", ""),
    "Deepgram": ("~$85M", 85, "Private", ""),
    "SOUNDBOKS": ("~$40M", 40, "Private", ""),
    "Lattice": ("~$344M", 344, "Private", ""),
    "Mux": ("~$100M", 100, "Private", ""),
    "Human Interest": ("~$502M", 502, "Private", ""),
    "Flirtey (SkyDrop)": ("~$16M", 16, "Private", ""),
    "Eight Sleep": ("~$160M", 160, "Private", ""),
    "Instawork": ("~$60M", 60, "Private", ""),
    "Cofactor Genomics": ("~$37M", 37, "Private", ""),
    "Click & Grow": ("~$10M", 10, "Private", ""),
    "Bitmovin": ("~$62M", 62, "Private", ""),
    "TetraScience": ("~$100M", 100, "Private", ""),
    "The Ticket Fairy": ("~$3M", 3, "Private", ""),
    "Font Awesome": ("~$10.8M", 10.8, "Private", "Kickstarter-funded"),
    "80,000 Hours": ("N/A", None, "Nonprofit", "Donation-funded"),
    "Xendit": ("~$538M", 538, "Private", "Southeast Asia payments"),
    "Shred Video": ("Unknown", None, "Private", ""),
    "Shape (ShapeScale)": ("~$2.5M", 2.5, "Private", ""),
    "RedCarpetUp": ("~$7M", 7, "Private", "India fintech"),
    "Plate IQ": ("~$35M", 35, "Private", ""),
    "PickTrace": ("~$12M", 12, "Private", ""),
    "Fountain": ("~$185M", 185, "Private", ""),
    "Microhealth": ("Unknown", None, "Private", ""),
    "Zeplin": ("~$32M", 32, "Private", ""),
    "Markhor": ("~$1M", 1, "Private", "Kickstarter-originated"),
    "Circle Medical": ("~$90M", 90, "Private", ""),
    "GiveCampus": ("~$61M", 61, "Private", ""),
    "Drip Capital": ("~$415M", 415, "Private", "Trade finance"),
    "Chaldal": ("~$10M", 10, "Private", "Bangladesh grocery"),
    "Clerky": ("~$3M", 3, "Private", "Bootstrapped"),
    "Bodyport": ("~$15M", 15, "Private", ""),
    "Verge Genomics": ("~$122M", 122, "Private", ""),
    "Thrive Agritech": ("~$30M", 30, "Private", ""),
    "Tesorio": ("~$17M", 17, "Private", ""),
    "AgileMD": ("~$10M", 10, "Private", ""),
    "Reach": ("Unknown", None, "Private", ""),
    "SunFarmer": ("~$2M", 2, "Private", "Solar · Nepal"),
    "Confident LIMS": ("Unknown", None, "Private", ""),
    "Branch8": ("Unknown", None, "Private", "E-commerce Asia"),
    "Heroic Labs": ("~$30M", 30, "Private", ""),
    "SnapMagic": ("~$10M", 10, "Private", ""),
    "Scope AR": ("~$11M", 11, "Private", ""),
    "PartnerStack": ("~$120M", 120, "Private", ""),
    "Assembly": ("~$7M", 7, "Private", ""),
    "Gemnote": ("~$5M", 5, "Private", ""),
    "New Story": ("~$50M+", 50, "Nonprofit", "Donation/grant-funded"),
    "Ironclad": ("~$333M", 333, "Private", ""),
    "Leaders In Tech": ("Unknown", None, "Private", ""),
    "teaBOT": ("~$5M", 5, "Private", ""),
    "Teleport": ("~$110M", 110, "Private", ""),
    "Lugg": ("~$22M", 22, "Private", ""),
    "Shasqi": ("~$82M", 82, "Private", "Cancer therapeutics"),
    "Adyen": ("~$266M", 266, "Public", "AMS: ADYEN · IPO June 2018"),
    "BAE Systems, Inc.": ("N/A", None, "Public", "LSE: BA. · Large defense contractor"),
    "GameChanger": ("~$50M", 50, "Acquired", "Acquired by DICK'S Sporting Goods 2021"),
    "MassMutual": ("N/A", None, "Mutual Co.", "170+ year old mutual insurer"),
    "Teachable": ("~$12M", 12, "Acquired", "Acquired by Hotmart 2020"),
    "Riskified": ("~$229M", 229, "Public", "NYSE: RSKD · IPO July 2021"),
    "GlossGenius": ("~$60M", 60, "Private", ""),
    "Dandy": ("~$170M", 170, "Private", ""),
    "Upstart": ("~$160M", 160, "Public", "NASDAQ: UPST · IPO Dec 2020"),
    "Radar": ("~$86M", 86, "Private", ""),
    "Chime": ("~$2.3B", 2300, "Private", "Valued $25B (2021)"),
    "Smartling": ("~$180M", 180, "Private", ""),
    "Current": ("~$220M", 220, "Private", ""),
    "Superblocks": ("~$37M", 37, "Private", ""),
    "Collectors": ("~$110M", 110, "Private", ""),
    "Granted": ("Unknown", None, "Private", ""),
    "Spot & Tango": ("~$39M", 39, "Private", ""),
    "Findigs, Inc.": ("~$27M", 27, "Private", ""),
    "Squarespace": ("~$578M", 578, "Private", "IPO May 2021 · taken private by Permira 2024 for $6.9B"),
    "firsthand Health Inc": ("~$160M", 160, "Private", ""),
    "Zepto": ("~$900M", 900, "Private", "Quick commerce · India"),
}

# ── Clean name (strip appended location from YC entries) ──────────────────────
def clean_name(raw):
    s = re.sub(r'(San Francisco|New York|Los Angeles|Boston|Chicago|Seattle|Austin|'
               r'Palo Alto|Sunnyvale|Menlo Park|Oakland|Berkeley|Redwood City|'
               r'Santa Clara|Emeryville|South San Francisco|San Leandro|San Mateo|'
               r'Lehi|Atlanta|Durango|Mountain View|Reno|Silver Spring|Bentonville|'
               r'Washington|Bogot[aá]|Lagos|Bengaluru|Mumbai|Jakarta|Copenhagen|'
               r'Amsterdam|London|Toronto|Kathmandu|Dhaka|Kowloon|Richmond|Newark|'
               r'Columbia|Kitchener|Gurugram|St\. Louis|Dakar).*, .*', '', raw).strip()
    s = re.sub(r'(?<=[a-z])([A-Z][a-zA-Z\s]+,\s+[A-Z]{2},?\s+.*)', '', s).strip()
    return s or raw.strip()

# ── Load, enrich, and prune startups ─────────────────────────────────────────
def batch_year(batch_str):
    """Extract 4-digit year from batch strings like 'Winter 2026', 'W21', 'S20'."""
    if not batch_str:
        return None
    m = re.search(r'(20\d{2})', batch_str)
    if m:
        return int(m.group(1))
    m = re.match(r'[WSFXwsfx](\d{2})$', batch_str.strip())
    if m:
        return 2000 + int(m.group(1))
    return None

with open('startups.json') as f:
    raw_startups = json.load(f)

enriched = []
pruned = []
for s in raw_startups:
    name = clean_name(s['name'])
    # For YC companies prefer batch year; fall back to FOUNDED dict
    byear = batch_year(s.get('batch', ''))
    fyear = FOUNDED.get(name)
    year = byear or fyear
    s2 = dict(s)
    s2['clean_name'] = name
    s2['founded'] = year
    enriched.append(s2)
    if year and year >= 2020:
        pruned.append(s2)

print(f"Total startups: {len(enriched)}")
print(f"Founded 2020+: {len(pruned)}")
for p in pruned:
    print(f"  {p['founded']} · {p['clean_name']}")

# Save pruned list
with open('startups.json', 'w') as f:
    json.dump(pruned, f, indent=2)
print("startups.json updated with 2020+ companies only.")

# ── Regenerate map ────────────────────────────────────────────────────────────
map_gen.generate_map()

# ── Build report table rows ───────────────────────────────────────────────────
STATUS_COLOR = {
    "Public":    ("#d1fae5", "#065f46"),
    "Private":   ("#dbeafe", "#1e40af"),
    "Acquired":  ("#ede9fe", "#5b21b6"),
    "Defunct":   ("#fee2e2", "#991b1b"),
    "Nonprofit": ("#fef3c7", "#92400e"),
    "Subsidiary":("#f3f4f6", "#374151"),
    "Mutual Co.":("#f3f4f6", "#374151"),
    "Unknown":   ("#f3f4f6", "#6b7280"),
}

def status_badge(status):
    bg, fg = STATUS_COLOR.get(status, ("#f3f4f6", "#374151"))
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:99px;font-size:11px;font-weight:600;white-space:nowrap">'
            f'{status}</span>')

def source_badge(source):
    if source == "Y Combinator":
        return '<span style="background:#fff3e0;color:#e65100;padding:2px 7px;border-radius:99px;font-size:10px;font-weight:700">YC</span>'
    elif source == "Built In NYC":
        return '<span style="background:#e3f2fd;color:#0277bd;padding:2px 7px;border-radius:99px;font-size:10px;font-weight:700">BNYC</span>'
    return source

rows = []
for s in pruned:
    name = s['clean_name']
    fd = FUNDING.get(name, ("Unknown", None, "Unknown", ""))
    funding_display, funding_millions, status, notes = fd
    rows.append({
        "name": name,
        "description": s.get("description", ""),
        "url": s.get("url", ""),
        "source": s.get("source", ""),
        "founded": s.get("founded", ""),
        "funding_display": funding_display,
        "funding_millions": funding_millions if funding_millions is not None else -1,
        "status": status,
        "notes": notes,
    })

tr_html = ""
for i, r in enumerate(rows, 1):
    url = r["url"]
    name_cell = (f'<a href="{url}" target="_blank" style="color:#1d4ed8;font-weight:600;'
                 f'text-decoration:none">{r["name"]}</a>' if url else
                 f'<span style="font-weight:600">{r["name"]}</span>')
    tr_html += (
        f'<tr data-funding="{r["funding_millions"]}" data-status="{r["status"]}">'
        f'<td style="width:30px;color:#9ca3af;font-size:12px">{i}</td>'
        f'<td>{name_cell}</td>'
        f'<td style="color:#6b7280;font-size:13px">{r["description"]}</td>'
        f'<td style="text-align:center;color:#64748b;font-size:13px">{r["founded"] or "—"}</td>'
        f'<td style="font-weight:600;white-space:nowrap">{r["funding_display"]}</td>'
        f'<td>{status_badge(r["status"])}</td>'
        f'<td style="font-size:12px;color:#6b7280">{r["notes"]}</td>'
        f'<td>{source_badge(r["source"])}</td>'
        f'</tr>\n'
    )

# ── HTML snippets to inject ───────────────────────────────────────────────────
INJECT_STYLE = """
<style>
#tab-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 10000;
    background: #fff; border-bottom: 1px solid #e5e7eb;
    display: flex; align-items: center; gap: 4px;
    padding: 0 16px; height: 44px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.tab-btn {
    padding: 6px 18px; border: none; background: none; cursor: pointer;
    font-size: 14px; font-weight: 500; color: #6b7280; border-radius: 6px;
    transition: all 0.15s;
}
.tab-btn:hover { background: #f3f4f6; color: #111; }
.tab-btn.active { background: #eff6ff; color: #1d4ed8; font-weight: 700; }
#pane-map { display: block; }
#pane-report {
    display: none; position: fixed;
    top: 44px; left: 0; right: 0; bottom: 0;
    overflow-y: auto; background: #f9fafb;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
#report-inner { max-width: 1200px; margin: 0 auto; padding: 24px 20px 60px; }
#report-inner h2 { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
#report-inner .subtitle { color: #6b7280; font-size: 14px; margin-bottom: 20px; }
#startup-table { width: 100%; border-collapse: collapse; background: #fff;
    border-radius: 10px; overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07); font-size: 14px; }
#startup-table thead th {
    background: #f8fafc; padding: 10px 14px; text-align: left;
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .05em; color: #64748b; border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}
#startup-table thead th.sortable { cursor: pointer; user-select: none; }
#startup-table thead th.sortable:hover { background: #f1f5f9; color: #1d4ed8; }
#startup-table thead th.sort-asc::after { content: " ▲"; }
#startup-table thead th.sort-desc::after { content: " ▼"; }
#startup-table tbody tr { border-bottom: 1px solid #f1f5f9; transition: background 0.1s; }
#startup-table tbody tr:last-child { border-bottom: none; }
#startup-table tbody tr:hover { background: #f8fafc; }
#startup-table td { padding: 10px 14px; vertical-align: middle; }
#filter-bar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
#search-box {
    flex: 1; min-width: 200px; padding: 8px 14px; border: 1px solid #d1d5db;
    border-radius: 8px; font-size: 14px; outline: none;
}
#search-box:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px #dbeafe; }
.filter-btn {
    padding: 7px 14px; border: 1px solid #d1d5db; background: #fff;
    border-radius: 8px; cursor: pointer; font-size: 13px; color: #374151;
    transition: all 0.1s;
}
.filter-btn:hover, .filter-btn.active { background: #eff6ff; border-color: #93c5fd; color: #1d4ed8; }
#legend { z-index: 9999; }
#pane-map {
    position: fixed !important;
    top: 44px; left: 0; right: 0; bottom: 0;
}
.folium-map {
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
}
</style>
"""

TAB_NAV = f"""
<div id="tab-bar">
  <span style="font-weight:800;font-size:15px;margin-right:10px;color:#111">🗽 NYC Startups</span>
  <button class="tab-btn active" onclick="switchTab('map')">🗺 Map</button>
  <button class="tab-btn" onclick="switchTab('report')">📋 Report</button>
</div>
"""

REPORT_PANE = f"""
<div id="pane-report">
  <div id="report-inner">
    <h2>NYC Startup Dossier</h2>
    <p class="subtitle">{len(pruned)} companies founded 2020+ · Funding data as of 2025 · Click column headers to sort</p>
    <div id="filter-bar">
      <input id="search-box" type="text" placeholder="Search companies..." oninput="applyFilters()">
      <button class="filter-btn active" onclick="setFilter('all',this)">All</button>
      <button class="filter-btn" onclick="setFilter('Private',this)">Private</button>
      <button class="filter-btn" onclick="setFilter('Public',this)">Public</button>
      <button class="filter-btn" onclick="setFilter('Acquired',this)">Acquired</button>
      <button class="filter-btn" onclick="setFilter('Defunct',this)">Defunct</button>
    </div>
    <table id="startup-table">
      <thead>
        <tr>
          <th>#</th>
          <th class="sortable" data-col="name">Company</th>
          <th>Description</th>
          <th class="sortable" data-col="founded" style="text-align:center">Founded</th>
          <th class="sortable sort-desc" data-col="funding">Funding</th>
          <th class="sortable" data-col="status">Status</th>
          <th>Notes</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody id="table-body">
{tr_html}
      </tbody>
    </table>
    <p style="text-align:center;color:#9ca3af;font-size:12px;margin-top:20px">
      Funding data sourced from training knowledge (cutoff Aug 2025). Cross-reference with
      <a href="https://www.crunchbase.com" target="_blank" style="color:#3b82f6">Crunchbase</a> for latest figures.
    </p>
  </div>
</div>
"""

TAB_JS = """
<script>
(function() {
  // ── Tab switching ─────────────────────────────────────────────────────────
  window.switchTab = function(tab) {
    var mapPane  = document.getElementById('pane-map');
    var repPane  = document.getElementById('pane-report');
    var legend   = document.getElementById('legend');
    var btns     = document.querySelectorAll('.tab-btn');
    btns.forEach(function(b){ b.classList.remove('active'); });
    if (tab === 'map') {
      mapPane.style.display  = 'block';
      repPane.style.display  = 'none';
      if (legend) legend.style.display = 'block';
      btns[0].classList.add('active');
    } else {
      mapPane.style.display  = 'none';
      repPane.style.display  = 'block';
      if (legend) legend.style.display = 'none';
      btns[1].classList.add('active');
    }
  };

  // ── Sort ──────────────────────────────────────────────────────────────────
  var sortState = { col: 'funding', dir: -1 };

  document.querySelectorAll('#startup-table thead th.sortable').forEach(function(th) {
    th.addEventListener('click', function() {
      var col = th.dataset.col;
      var dir = (sortState.col === col) ? -sortState.dir : -1;
      sortState = { col: col, dir: dir };
      document.querySelectorAll('#startup-table thead th').forEach(function(h) {
        h.classList.remove('sort-asc','sort-desc');
      });
      th.classList.add(dir === 1 ? 'sort-asc' : 'sort-desc');
      sortRows(col, dir);
    });
  });

  function sortRows(col, dir) {
    var tbody = document.getElementById('table-body');
    var rows  = Array.from(tbody.querySelectorAll('tr'));
    rows.sort(function(a, b) {
      if (col === 'funding') {
        var av = parseFloat(a.dataset.funding);
        var bv = parseFloat(b.dataset.funding);
        if (av < 0 && bv < 0) return 0;
        if (av < 0) return 1;
        if (bv < 0) return -1;
        return dir * (bv - av);
      } else if (col === 'name') {
        var at = a.cells[1].textContent.trim().toLowerCase();
        var bt = b.cells[1].textContent.trim().toLowerCase();
        return dir * at.localeCompare(bt);
      } else if (col === 'status') {
        var at = a.dataset.status.toLowerCase();
        var bt = b.dataset.status.toLowerCase();
        return dir * at.localeCompare(bt);
      } else if (col === 'founded') {
        var av = parseInt(a.cells[3].textContent) || 0;
        var bv = parseInt(b.cells[3].textContent) || 0;
        return dir * (bv - av);
      }
      return 0;
    });
    rows.forEach(function(r){ tbody.appendChild(r); });
    renumber();
  }

  function renumber() {
    var visible = document.querySelectorAll('#table-body tr:not([style*="display: none"])');
    visible.forEach(function(r, i){ r.cells[0].textContent = i + 1; });
  }

  // ── Filter ────────────────────────────────────────────────────────────────
  var activeFilter = 'all';

  window.setFilter = function(status, btn) {
    activeFilter = status;
    document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    applyFilters();
  };

  window.applyFilters = function() {
    var query = document.getElementById('search-box').value.toLowerCase();
    document.querySelectorAll('#table-body tr').forEach(function(r) {
      var text   = r.textContent.toLowerCase();
      var status = r.dataset.status;
      var matchQ = !query || text.includes(query);
      var matchF = activeFilter === 'all' || status === activeFilter;
      r.style.display = (matchQ && matchF) ? '' : 'none';
    });
    renumber();
  };

  // Default sort on load
  document.addEventListener('DOMContentLoaded', function() {
    sortRows('funding', -1);
  });
})();
</script>
"""

# ── Read & patch the freshly generated HTML ───────────────────────────────────
with open('nyc_ai_startups_map.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('</head>', INJECT_STYLE + '</head>', 1)
html = html.replace('<body>', '<body>\n' + TAB_NAV + '\n<div id="pane-map">', 1)
html = html.replace('</body>', '</div>' + REPORT_PANE + '\n</body>', 1)
html += TAB_JS

with open('nyc_ai_startups_map.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Done! Map + Report tab injected into nyc_ai_startups_map.html")
print(f"  → {len(pruned)} companies in report (founded 2020+), sortable by funding/name/status/year")
