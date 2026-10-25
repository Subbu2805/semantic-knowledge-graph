#!/usr/bin/env python3
"""Generates the synthetic, deterministic CSV corpora used by the real-world use cases.

Each corpus models a domain where the Semantic Knowledge Graph is commonly applied.
Entities are drawn from weighted, correlated distributions (e.g. job titles imply
skills, symptoms imply conditions) plus domain-wide "noise" values that are popular
everywhere, so relatedness and popularity diverge the way they do on real data.

Usage: python3 datasets/generate.py [output_dir]   (defaults to this directory)
"""
import csv
import os
import random
import sys

SEED = 20161017


def pick(rng, weighted, k):
    """Picks k distinct items from a {item: weight} dict."""
    items = list(weighted.items())
    chosen = []
    while items and len(chosen) < k:
        total = sum(w for _, w in items)
        r = rng.uniform(0, total)
        acc = 0
        for i, (item, w) in enumerate(items):
            acc += w
            if acc >= r:
                chosen.append(item)
                items.pop(i)
                break
    return chosen


def mix(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


def write(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for row in rows:
            w.writerow(["|".join(c) if isinstance(c, list) else c for c in row])


# --------------------------------------------------------------------------- jobs
JOB_PROFILES = {
    "Data Scientist": dict(w=8, industry={"Technology": 5, "Finance": 3, "Healthcare": 2, "Retail": 2},
        skills={"Python": 10, "Machine Learning": 10, "Statistics": 8, "SQL": 6, "Deep Learning": 4,
                "TensorFlow": 3, "PyTorch": 3, "R": 4, "Apache Spark": 3, "Data Visualization": 4,
                "Generative AI": 2, "Large Language Models": 2}),
    "Data Engineer": dict(w=7, industry={"Technology": 6, "Finance": 3, "Retail": 2},
        skills={"Python": 7, "SQL": 9, "Apache Spark": 8, "Apache Kafka": 6, "Airflow": 6, "AWS": 5,
                "Snowflake": 4, "dbt": 4, "Scala": 3, "Data Modeling": 5}),
    "Machine Learning Engineer": dict(w=6, industry={"Technology": 8, "Finance": 2},
        skills={"Python": 10, "Machine Learning": 8, "PyTorch": 6, "TensorFlow": 5, "Kubernetes": 4,
                "MLOps": 6, "Docker": 5, "Large Language Models": 5, "Generative AI": 4, "AWS": 3}),
    "Software Engineer": dict(w=12, industry={"Technology": 8, "Finance": 3, "Retail": 2, "Healthcare": 1},
        skills={"Java": 8, "Python": 5, "JavaScript": 6, "Git": 7, "REST APIs": 6, "Microservices": 5,
                "Docker": 4, "Kubernetes": 3, "Go": 3, "Spring Boot": 4, "System Design": 4}),
    "Frontend Developer": dict(w=6, industry={"Technology": 6, "Retail": 3, "Media": 2},
        skills={"JavaScript": 10, "TypeScript": 8, "React": 9, "CSS": 7, "HTML": 7, "Next.js": 4,
                "Accessibility": 3, "Figma": 2, "Git": 4}),
    "DevOps Engineer": dict(w=6, industry={"Technology": 7, "Finance": 2},
        skills={"Kubernetes": 9, "Docker": 8, "Terraform": 8, "AWS": 7, "CI/CD": 8, "Linux": 7,
                "Prometheus": 4, "Bash": 5, "Python": 3, "Ansible": 4}),
    "Security Engineer": dict(w=4, industry={"Technology": 5, "Finance": 4, "Government": 3},
        skills={"Network Security": 8, "SIEM": 6, "Penetration Testing": 6, "Incident Response": 7,
                "Cloud Security": 6, "Python": 3, "Linux": 4, "Threat Modeling": 4, "AWS": 2}),
    "Product Manager": dict(w=6, industry={"Technology": 7, "Finance": 2, "Retail": 2},
        skills={"Product Strategy": 9, "Roadmapping": 8, "Agile": 7, "Stakeholder Management": 7,
                "User Research": 5, "SQL": 3, "A/B Testing": 4, "Jira": 4}),
    "Account Manager": dict(w=7, industry={"Retail": 3, "Technology": 3, "Manufacturing": 3, "Finance": 2},
        skills={"Account Management": 10, "Salesforce": 7, "Negotiation": 7, "Customer Retention": 6,
                "B2B Sales": 6, "Upselling": 5, "CRM": 6}),
    "Sales Representative": dict(w=8, industry={"Retail": 5, "Manufacturing": 3, "Technology": 2},
        skills={"B2B Sales": 8, "Cold Calling": 7, "Lead Generation": 7, "Salesforce": 5, "Negotiation": 6,
                "CRM": 5, "Prospecting": 6}),
    "Registered Nurse": dict(w=9, industry={"Healthcare": 10},
        skills={"Patient Care": 10, "BLS Certification": 8, "ACLS": 6, "Electronic Health Records": 6,
                "Medication Administration": 7, "Triage": 5, "Critical Care": 3}),
    "Financial Analyst": dict(w=6, industry={"Finance": 9, "Manufacturing": 2, "Retail": 1},
        skills={"Financial Modeling": 9, "Excel": 9, "Forecasting": 7, "SQL": 4, "Budgeting": 6,
                "Valuation": 5, "Power BI": 4, "Accounting": 4}),
    "Marketing Manager": dict(w=5, industry={"Retail": 4, "Media": 4, "Technology": 3},
        skills={"Digital Marketing": 9, "SEO": 7, "Content Strategy": 6, "Google Analytics": 6,
                "Social Media Marketing": 6, "Marketing Automation": 4, "A/B Testing": 3, "Branding": 4}),
    "Truck Driver": dict(w=6, industry={"Logistics": 10},
        skills={"CDL Class A": 10, "DOT Regulations": 7, "Route Planning": 5, "Forklift": 3,
                "Hazmat Endorsement": 4, "Logbook Management": 5}),
}
GENERIC_SKILLS = {"Communication": 10, "Microsoft Office": 7, "Teamwork": 8, "Problem Solving": 8,
                  "Customer Service": 4}
SENIORITY = {"Entry Level": 3, "Mid Level": 5, "Senior": 4, "Lead": 2, "Director": 1}
LOCATIONS = {"New York, NY": 8, "San Francisco, CA": 6, "Seattle, WA": 4, "Austin, TX": 4, "Chicago, IL": 5,
             "Atlanta, GA": 4, "Boston, MA": 4, "Denver, CO": 3, "Remote": 7}
TECH_HUB = {"San Francisco, CA": 6, "Seattle, WA": 5, "Remote": 5}
# skills whose demand grows over the years -> "emerging skills" use case
EMERGING = {"Generative AI": {2024: 0.3, 2025: 1.0, 2026: 2.5}, "Large Language Models": {2024: 0.3, 2025: 1.2, 2026: 2.5},
            "MLOps": {2024: 0.6, 2025: 1.0, 2026: 1.5}, "Next.js": {2024: 0.5, 2025: 1.0, 2026: 1.6},
            "dbt": {2024: 0.6, 2025: 1.0, 2026: 1.5}, "Hadoop": {2024: 1.5, 2025: 0.6, 2026: 0.2}}


def jobs(rng, n=4000):
    titles = {t: p["w"] for t, p in JOB_PROFILES.items()}
    for i in range(1, n + 1):
        title = pick(rng, titles, 1)[0]
        p = JOB_PROFILES[title]
        year = pick(rng, {2024: 3, 2025: 4, 2026: 4}, 1)[0]
        weights = dict(p["skills"])
        if title in ("Data Scientist", "Data Engineer"):
            weights["Hadoop"] = 4
        for s, by_year in EMERGING.items():
            if s in weights:
                weights[s] *= by_year[year]
        skills = pick(rng, weights, rng.randint(4, 7)) + pick(rng, GENERIC_SKILLS, rng.randint(1, 3))
        industry = pick(rng, p["industry"], 1)
        loc_weights = mix(LOCATIONS, TECH_HUB) if industry[0] == "Technology" else LOCATIONS
        location = pick(rng, loc_weights, 1)
        seniority = pick(rng, SENIORITY, 1)
        content = (f"{seniority[0]} {title} wanted in {location[0]} for a {industry[0].lower()} company. "
                   f"You will work with {', '.join(skills[:4])} and {skills[4] if len(skills) > 4 else 'more'}.")
        yield [f"job-{i}", content, [title], skills, industry, location, seniority, str(year)]


# --------------------------------------------------------------------- ecommerce
CATEGORIES = {
    "Running Shoes": dict(w=8, price={"$50-$100": 4, "$100-$200": 5, "$200+": 1},
        brands={"Nike": 6, "Adidas": 5, "Brooks": 5, "Asics": 4, "Hoka": 4, "New Balance": 3},
        attrs={"Breathable Mesh": 6, "Cushioned": 7, "Lightweight": 6, "Neutral Support": 4, "Stability": 3, "Waterproof": 1},
        terms={"running shoes": 10, "marathon shoes": 4, "cushioned sneakers": 4, "jogging shoes": 4, "best running shoes": 3}),
    "Trail Shoes": dict(w=4, price={"$100-$200": 6, "$200+": 2},
        brands={"Salomon": 7, "Hoka": 4, "Merrell": 5, "Brooks": 2},
        attrs={"Waterproof": 7, "Grippy Outsole": 8, "Rock Plate": 4, "Gore-Tex": 5, "Cushioned": 3},
        terms={"trail running shoes": 8, "hiking shoes": 5, "waterproof trail shoes": 5, "running shoes": 2}),
    "Yoga Mats": dict(w=4, price={"Under $50": 6, "$50-$100": 4, "$100-$200": 1},
        brands={"Manduka": 6, "Lululemon": 6, "Gaiam": 5, "Liforme": 3},
        attrs={"Non-Slip": 8, "Eco-Friendly": 6, "Extra Thick": 5, "Lightweight": 3},
        terms={"yoga mat": 10, "non slip yoga mat": 5, "exercise mat": 4, "pilates mat": 3}),
    "Gaming Laptops": dict(w=5, price={"$1000-$2000": 6, "$2000+": 4},
        brands={"ASUS ROG": 6, "Razer": 4, "MSI": 5, "Alienware": 4, "Lenovo Legion": 4},
        attrs={"RTX 4070": 5, "RTX 4090": 3, "144Hz Display": 7, "RGB Keyboard": 6, "32GB RAM": 4, "1TB SSD": 5},
        terms={"gaming laptop": 10, "cheap gaming laptop": 4, "rtx laptop": 5, "laptop": 3}),
    "Business Laptops": dict(w=5, price={"$500-$1000": 4, "$1000-$2000": 5},
        brands={"Lenovo ThinkPad": 7, "Dell XPS": 5, "Apple MacBook": 7, "HP EliteBook": 4},
        attrs={"Long Battery Life": 8, "Lightweight": 6, "16GB RAM": 6, "1TB SSD": 3, "Fingerprint Reader": 4},
        terms={"laptop": 10, "work laptop": 5, "ultrabook": 4, "macbook": 4, "thin and light laptop": 4}),
    "Wireless Headphones": dict(w=7, price={"Under $50": 2, "$50-$100": 3, "$100-$200": 4, "$200+": 4},
        brands={"Sony": 7, "Bose": 7, "Apple": 6, "Sennheiser": 3, "JBL": 4, "Anker": 3},
        attrs={"Noise Cancelling": 9, "Bluetooth 5.3": 6, "30h Battery": 5, "Over-Ear": 5, "In-Ear": 4, "Water Resistant": 2},
        terms={"noise cancelling headphones": 8, "wireless headphones": 10, "earbuds": 5, "bluetooth headphones": 6}),
    "Smartwatches": dict(w=5, price={"$100-$200": 4, "$200+": 6},
        brands={"Apple": 8, "Garmin": 6, "Samsung": 5, "Fitbit": 4},
        attrs={"Heart Rate Monitor": 8, "GPS": 7, "Water Resistant": 6, "Sleep Tracking": 6, "ECG": 3},
        terms={"smartwatch": 10, "fitness tracker": 6, "running watch": 4, "gps watch": 4}),
    "Coffee Makers": dict(w=5, price={"Under $50": 3, "$50-$100": 4, "$100-$200": 3, "$200+": 2},
        brands={"Breville": 5, "Keurig": 6, "De'Longhi": 4, "Nespresso": 5, "Cuisinart": 4},
        attrs={"Programmable": 6, "Single Serve": 5, "Built-in Grinder": 4, "Milk Frother": 4, "Thermal Carafe": 3},
        terms={"coffee maker": 10, "espresso machine": 6, "single serve coffee": 4, "drip coffee maker": 4}),
    "Camping Tents": dict(w=4, price={"$50-$100": 3, "$100-$200": 5, "$200+": 3},
        brands={"REI Co-op": 5, "Coleman": 6, "Big Agnes": 4, "MSR": 3},
        attrs={"Waterproof": 8, "Lightweight": 5, "4-Person": 4, "2-Person": 5, "Easy Setup": 6},
        terms={"camping tent": 10, "backpacking tent": 5, "family tent": 4, "waterproof tent": 3}),
}
GENERIC_ATTRS = {"Free Shipping": 8, "Best Seller": 4, "Gift Idea": 3}
GENERIC_TERMS = {"deals": 5, "sale": 4, "gift for him": 2, "gift for her": 2}


def ecommerce(rng, n=4000):
    cats = {c: p["w"] for c, p in CATEGORIES.items()}
    for i in range(1, n + 1):
        cat = pick(rng, cats, 1)[0]
        p = CATEGORIES[cat]
        brand = pick(rng, p["brands"], 1)
        attrs = pick(rng, p["attrs"], rng.randint(2, 4)) + pick(rng, GENERIC_ATTRS, rng.randint(0, 2))
        terms = pick(rng, p["terms"], rng.randint(1, 3)) + pick(rng, GENERIC_TERMS, rng.randint(0, 1))
        price = pick(rng, p["price"], 1)
        content = f"{brand[0]} {cat[:-1] if cat.endswith('s') else cat} - {', '.join(attrs)}. Customers searched for {terms[0]}."
        yield [f"sku-{i}", content, [cat], brand, attrs, terms, price]


# -------------------------------------------------------------------- healthcare
CONDITIONS = {
    "Type 2 Diabetes": dict(w=8, specialty="Endocrinology", age={"Adult": 5, "Senior": 5},
        symptoms={"Increased Thirst": 8, "Frequent Urination": 8, "Fatigue": 5, "Blurred Vision": 4, "Slow Healing Wounds": 3},
        meds={"Metformin": 9, "Insulin Glargine": 4, "Empagliflozin": 3, "Semaglutide": 4}),
    "Hypertension": dict(w=10, specialty="Cardiology", age={"Adult": 5, "Senior": 7},
        symptoms={"Headache": 5, "Dizziness": 4, "Chest Pain": 2, "Shortness of Breath": 2, "Nosebleed": 2},
        meds={"Lisinopril": 8, "Amlodipine": 7, "Hydrochlorothiazide": 5, "Losartan": 5}),
    "Asthma": dict(w=6, specialty="Pulmonology", age={"Child": 6, "Adult": 4},
        symptoms={"Wheezing": 9, "Shortness of Breath": 8, "Chest Tightness": 6, "Cough": 7},
        meds={"Albuterol": 9, "Fluticasone": 6, "Montelukast": 4, "Budesonide": 3}),
    "Migraine": dict(w=6, specialty="Neurology", age={"Adult": 8, "Child": 1},
        symptoms={"Headache": 10, "Nausea": 6, "Light Sensitivity": 7, "Visual Aura": 4, "Dizziness": 2},
        meds={"Sumatriptan": 8, "Ibuprofen": 5, "Topiramate": 3, "Rimegepant": 2}),
    "Major Depressive Disorder": dict(w=6, specialty="Psychiatry", age={"Adult": 8, "Senior": 2, "Child": 1},
        symptoms={"Persistent Sadness": 9, "Fatigue": 6, "Insomnia": 6, "Loss of Interest": 7, "Weight Change": 3},
        meds={"Sertraline": 8, "Escitalopram": 6, "Bupropion": 4, "Fluoxetine": 4}),
    "Influenza": dict(w=7, specialty="Primary Care", age={"Child": 4, "Adult": 5, "Senior": 3},
        symptoms={"Fever": 10, "Cough": 7, "Muscle Aches": 7, "Fatigue": 6, "Sore Throat": 5},
        meds={"Oseltamivir": 7, "Acetaminophen": 6, "Ibuprofen": 4}),
    "COVID-19": dict(w=5, specialty="Primary Care", age={"Child": 2, "Adult": 6, "Senior": 4},
        symptoms={"Fever": 8, "Cough": 8, "Loss of Taste or Smell": 7, "Fatigue": 6, "Shortness of Breath": 4},
        meds={"Nirmatrelvir/Ritonavir": 6, "Acetaminophen": 6, "Dexamethasone": 2}),
    "Osteoarthritis": dict(w=6, specialty="Rheumatology", age={"Senior": 8, "Adult": 3},
        symptoms={"Joint Pain": 10, "Joint Stiffness": 8, "Swelling": 5, "Reduced Range of Motion": 5},
        meds={"Naproxen": 6, "Acetaminophen": 5, "Diclofenac Gel": 4, "Ibuprofen": 4}),
    "GERD": dict(w=5, specialty="Gastroenterology", age={"Adult": 7, "Senior": 4},
        symptoms={"Heartburn": 10, "Regurgitation": 7, "Chest Pain": 4, "Cough": 2, "Nausea": 3},
        meds={"Omeprazole": 9, "Pantoprazole": 5, "Famotidine": 5}),
    "Iron Deficiency Anemia": dict(w=4, specialty="Hematology", age={"Adult": 6, "Child": 2, "Senior": 2},
        symptoms={"Fatigue": 9, "Pale Skin": 6, "Shortness of Breath": 3, "Dizziness": 4, "Cold Hands": 4},
        meds={"Ferrous Sulfate": 9, "Vitamin C": 3}),
}


def healthcare(rng, n=3000):
    conds = {c: p["w"] for c, p in CONDITIONS.items()}
    for i in range(1, n + 1):
        primary = pick(rng, conds, 1)[0]
        cs = [primary]
        if rng.random() < 0.3:  # comorbidity, biased toward metabolic/cardio pairing
            extra = "Hypertension" if primary == "Type 2 Diabetes" and rng.random() < 0.7 else pick(rng, conds, 1)[0]
            if extra not in cs:
                cs.append(extra)
        symptoms, meds = [], []
        for c in cs:
            p = CONDITIONS[c]
            symptoms += [s for s in pick(rng, p["symptoms"], rng.randint(2, 4)) if s not in symptoms]
            meds += [m for m in pick(rng, p["meds"], rng.randint(1, 2)) if m not in meds]
        p = CONDITIONS[primary]
        age = pick(rng, p["age"], 1)
        content = (f"{age[0]} patient presenting with {', '.join(s.lower() for s in symptoms)}. "
                   f"Assessment: {', '.join(cs)}. Plan: {', '.join(meds)}.")
        yield [f"enc-{i}", content, cs, symptoms, meds, [p["specialty"]], age]


# ----------------------------------------------------------------------- support
ISSUES = {
    "Login Failure": dict(w=8, product={"Mobile App": 5, "Web Dashboard": 5}, comp={"Authentication Service": 9, "SSO Integration": 5},
        team="Identity", res={"Password Reset": 6, "Configuration Change": 3, "Bug Fix Deployed": 2},
        text=["cannot log in", "login keeps failing", "SSO redirect loop", "2FA code not accepted"]),
    "Payment Declined": dict(w=6, product={"Billing": 9, "Mobile App": 2}, comp={"Payment Gateway": 9, "Fraud Detection": 4},
        team="Payments", res={"Card Updated": 6, "Refund Issued": 3, "Bug Fix Deployed": 2},
        text=["card was declined", "payment failed at checkout", "charged twice", "invoice not paid"]),
    "App Crash": dict(w=7, product={"Mobile App": 10}, comp={"iOS Client": 6, "Android Client": 6, "Push Notifications": 2},
        team="Mobile", res={"Bug Fix Deployed": 7, "Workaround Provided": 4},
        text=["app crashes on launch", "app freezes", "crash after update", "app closes when opening camera"]),
    "Slow Performance": dict(w=6, product={"Web Dashboard": 7, "API": 4}, comp={"Search Service": 5, "Database": 6, "CDN": 3},
        team="Platform", res={"Infrastructure Scaled": 6, "Bug Fix Deployed": 3, "Workaround Provided": 2},
        text=["dashboard is very slow", "page takes forever to load", "timeouts on reports", "search is slow"]),
    "API Error": dict(w=5, product={"API": 10}, comp={"API Gateway": 8, "Rate Limiter": 6, "Webhooks": 4},
        team="Platform", res={"Configuration Change": 5, "Documentation Provided": 5, "Bug Fix Deployed": 3},
        text=["getting 500 errors from the API", "429 too many requests", "webhook not delivered", "API returns 401"]),
    "Data Export Issue": dict(w=4, product={"Web Dashboard": 8, "API": 2}, comp={"Reporting Service": 9, "Database": 3},
        team="Analytics", res={"Bug Fix Deployed": 5, "Workaround Provided": 5},
        text=["CSV export is empty", "report export fails", "missing rows in export"]),
    "Billing Question": dict(w=6, product={"Billing": 10}, comp={"Subscription Service": 8, "Invoicing": 6},
        team="Payments", res={"Documentation Provided": 7, "Refund Issued": 3, "Plan Changed": 4},
        text=["how do I change my plan", "question about my invoice", "cancel subscription", "upgrade pricing"]),
    "Notification Missing": dict(w=4, product={"Mobile App": 7, "Web Dashboard": 3}, comp={"Push Notifications": 9, "Email Service": 6},
        team="Mobile", res={"Configuration Change": 5, "Bug Fix Deployed": 5},
        text=["not receiving push notifications", "no email alerts", "notifications delayed"]),
}
RELEASES = {"v4.1": 5, "v4.2": 5, "v4.3": 5}


def support(rng, n=4000):
    iss = {k: p["w"] for k, p in ISSUES.items()}
    for i in range(1, n + 1):
        release = pick(rng, RELEASES, 1)[0]
        weights = dict(iss)
        if release == "v4.3":  # regression shipped in v4.3: Android crashes + push notifications
            weights["App Crash"] *= 3
            weights["Notification Missing"] *= 2.5
        issue = pick(rng, weights, 1)[0]
        p = ISSUES[issue]
        product = pick(rng, p["product"], 1)
        comp_w = dict(p["comp"])
        if release == "v4.3" and issue == "App Crash":
            comp_w["Android Client"] *= 4
        if release == "v4.3" and issue == "Notification Missing":
            comp_w["Push Notifications"] *= 3
        comp = pick(rng, comp_w, 1)
        res = pick(rng, p["res"], 1)
        content = f"Customer reports: {rng.choice(p['text'])} on {product[0].lower()} ({release}). Please help."
        yield [f"ticket-{i}", content, product, [issue], comp, [p["team"]], res, release]


CORPORA = {
    "jobs": (["id", "content", "jobtitle", "skills", "industry", "location", "seniority", "posted_year"], jobs),
    "ecommerce": (["id", "content", "category", "brand", "attributes", "search_terms", "price_band"], ecommerce),
    "healthcare": (["id", "content", "conditions", "symptoms", "medications", "specialty", "age_group"], healthcare),
    "support": (["id", "content", "product", "issue_type", "component", "team", "resolution", "release"], support),
}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    for name, (header, gen) in CORPORA.items():
        rng = random.Random(f"{SEED}-{name}")
        path = os.path.join(out, f"{name}.csv")
        write(path, header, gen(rng))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
