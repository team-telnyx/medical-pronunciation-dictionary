"""
Curated medical term lists for pronunciation dictionary.

Sources:
- Top prescribed drugs: CDC NHCS public data + clinical knowledge
- Clinical terms: high-frequency diagnoses and procedures from SNOMED CT subsets
- Anatomical terms: standard anatomical terminology
- Medical acronyms: manually curated from clinical documentation

Each list contains terms that are frequently mispronounced by TTS engines.
"""

# Top 250 most prescribed drugs in the US (generic + key brand names)
# These are the drugs most likely to appear in healthcare voice AI conversations.
# Prioritized by prescription volume and pronunciation difficulty.

TOP_DRUGS = [
    # Cardiovascular
    "atorvastatin", "Lipitor", "lisinopril", "metoprolol", "amlodipine",
    "losartan", "metoprolol succinate", "metoprolol tartrate", "carvedilol",
    "valsartan", "enalapril", "ramipril", "felodipine", "nimodipine",
    "nicardipine", "nitroglycerin", "hydralazine", "clonidine",
    "spironolactone", "furosemide", "hydrochlorothiazide", "triamterene",
    "bumetanide", "torsemide", "eplerenone", "diltiazem", "verapamil",
    "nifedipine", "doxazosin", "terazosin", "prazosin", "amiodarone",
    "dronedarone", "sotalol", "propafenone", "flecainide", "mexiletine",
    "hydralazine", "isosorbide dinitrate", "isosorbide mononitrate",
    "warfarin", "rivaroxaban", "apixaban", "dabigatran", "clopidogrel",
    "prasugrel", "ticagrelor", "ezetimibe", "fenofibrate", "gemfibrozil",
    "niacin", "colesevelam", "simvastatin", "rosuvastatin", "pravastatin",
    "fluvastatin", "pitavastatin", "alirocumab", "evolocumab",

    # Diabetes
    "metformin", "glipizide", "glyburide", "pioglitazone", "sitagliptin",
    "linagliptin", "saxagliptin", "alogliptin", "empagliflozin",
    "canagliflozin", "dapagliflozin", "semaglutide", "liraglutide",
    "exenatide", "dulaglutide", "tirzepatide", "insulin glargine",
    "insulin lispro", "insulin aspart", "insulin detemir", "insulin degludec",
    "acarbose", "miglitol", "repaglinide", "nateglinide",

    # Antibiotics
    "amoxicillin", "amoxicillin clavulanate", "azithromycin",
    "cephalexin", "ciprofloxacin", "clindamycin", "doxycycline",
    "metronidazole", "sulfamethoxazole trimethoprim", "nitrofurantoin",
    "penicillin", "vancomycin", "levofloxacin", "moxifloxacin",
    "cefdinir", "cefaclor", "cefuroxime", "ceftriaxone", "cefepime",
    "meropenem", "ertapenem", "imipenem", "piperacillin tazobactam",
    "gentamicin", "tobramycin", "amikacin", "linezolid", "daptomycin",
    "tigecycline", "minocycline", "rifampin", "isoniazid", "pyrazinamide",
    "ethambutol", "fluconazole", "ketoconazole", "itraconazole",
    "voriconazole", "posaconazole", "acyclovir", "valacyclovir",
    "famciclovir", "oseltamivir", "aciklovir",

    # Pain / NSAIDs
    "ibuprofen", "naproxen", "celecoxib", "meloxicam", "diclofenac",
    "ketorolac", "indomethacin", "nabumetone", "etodolac", "oxaprozin",
    "acetaminophen", "tramadol", "gabapentin", "pregabalin", "duloxetine",
    "amitriptyline", "nortriptyline", "topiramate", "carbamazepine",
    "oxcarbazepine", "lamotrigine", "levetiracetam", "phenytoin",
    "valproic acid", "zonisamide", "lacosamide", "rufinamide",

    # GI
    "omeprazole", "pantoprazole", "esomeprazole", "lansoprazole",
    "rabeprazole", "dexlansoprazole", "famotidine", "ranitidine",
    "cimetidine", "nizatidine", "aluminum hydroxide", "simethicone",
    "ondansetron", "granisetron", "palonosetron", "metoclopramide",
    "promethazine", "prochlorperazine", "loperamide", "docusate",
    "polyethylene glycol", "bisacodyl", "senna", "lactulose",

    # Respiratory
    "albuterol", "levalbuterol", "ipratropium", "tiotropium",
    "umeclidinium", "glycopyrrolate", "formoterol", "salmeterol",
    "indacaterol", "olodaterol", "fluticasone", "budesonide",
    "mometasone", "ciclesonide", "beclomethasone", "montelukast",
    "zafirlukast", "zileuton", "theophylline", "roflumilast",
    "benralizumab", "mepolizumab", "reslizumab", "dupilumab",
    "omalizumab",

    # Mental health
    "sertraline", "fluoxetine", "escitalopram", "citalopram",
    "paroxetine", "venlafaxine", "desvenlafaxine", "milnacipran",
    "bupropion", "mirtazapine", "trazodone", "nefazodone",
    "vortioxetine", "vilazodone", "fluvoxamine", "clomipramine",
    "desipramine", "imipramine", "protriptyline", "phenelzine",
    "tranylcypromine", "isocarboxazid", "selegiline", "rasagiline",
    "aripiprazole", "olanzapine", "quetiapine", "risperidone",
    "paliperidone", "ziprasidone", "lurasidone", "brexpiprazole",
    "cariprazine", "clozapine", "haloperidol", "chlorpromazine",
    "lithium", "valproate", "lamotrigine", "asenapine",
    "dexmethylphenidate", "lisdexamfetamine", "methylphenidate",
    "amfetamine", "guanfacine", "clonidine",

    # Oncology
    "tamoxifen", "anastrozole", "letrozole", "exemestane",
    "leuprolide", "goserelin", "triptorelin", "bicalutamide",
    "enzalutamide", "abiraterone", "imatinib", "dasatinib", "nilotinib",
    "bosutinib", "ponatinib", "ibrutinib", "acalabrutinib",
    "venetoclax", "rituximab", "trastuzumab", "pertuzumab",
    "bevacizumab", "cetuximab", "panitumumab", "pembrolizumab",
    "nivolumab", "ipilimumab", "atezolizumab", "durvalumab",
    "avelumab", "cisplatin", "carboplatin", "oxaliplatin",
    "paclitaxel", "docetaxel", "doxorubicin", "daunorubicin",
    "vincristine", "vinblastine", "vinorelbine", "etoposide",
    "cyclophosphamide", "ifosfamide", "methotrexate", "pemetrexed",
    "gemcitabine", "fluorouracil", "capecitabine", "cytarabine",

    # Immunology / Rheumatology
    "adalimumab", "etanercept", "infliximab", "certolizumab",
    "golimumab", "tocilizumab", "sarilumab", "rituximab",
    "ustekinumab", "secukinumab", "ixekizumab", "brodalumab",
    "guselkumab", "risankizumab", "tildrakizumab", "abatacept",
    "methotrexate", "leflunomide", "sulfasalazine", "hydroxychloroquine",
    "azathioprine", "mycophenolate", "tacrolimus", "cyclosporine",
    "sirolimus", "everolimus",

    # Neurology
    "levodopa", "carbidopa", "pramipexole", "ropinirole", "rotigotine",
    "amantadine", "entacapone", "rasagiline", "selegiline",
    "safinamide", "apomorphine", "donepezil", "rivastigmine",
    "galantamine", "memantine", "glatiramer", "fingolimod",
    "dimethyl fumarate", "teriflunomide", "ozanimod", "siponimod",
    "natalizumab", "ocrelizumab", "ofatumumab", "fumarate",

    # Other common
    "levothyroxine", "prednisone", "prednisolone", "methylprednisolone",
    "hydrocortisone", "dexamethasone", "fludrocortisone",
    "alendronate", "risedronate", "ibandronate", "zoledronic acid",
    "denosumab", "teriparatide", "raloxifene", "calcitonin",
    "tadalafil", "sildenafil", "vardenafil", "finasteride",
    "dutasteride", "tamsulosin", "silodosin", "alfuzosin",
    "oxybutynin", "tolterodine", "solifenacin", "darifenacin",
    "mirabegron", "phenazopyridine",
    "hydroxyzine", "fexofenadine", "loratadine", "cetirizine",
    "diphenhydramine", "chlorpheniramine", "azelastine", "olopatadine",
    "modafinil", "armodafinil", "sumatriptan", "rizatriptan",
    "zolmitriptan", "eletriptan", "almotriptan", "frovatriptan",
    "naratriptan", "ubrogepant", "rimegepant", "erenumab",
    "fremanezumab", "galcanezumab", "eprodual", "onabotulinumtoxinA",
    "epinephrine", "naloxone",
]

# Common medical acronyms - frequently spoken in clinical conversations
MEDICAL_ACRONYMS = [
    "MI", "COPD", "CHF", "UTI", "MRI", "CT", "EKG", "ECG", "EEG",
    "BUN", "CMP", "CBC", "TSH", "HbA1c", "PT", "INR", "PTT", "DVT",
    "PE", "CVA", "TIA", "ICU", "NICU", "ER", "ED", "OR", "PACU",
    "ICU", "CCU", "SICU", "MICU", "BP", "HR", "RR", "SpO2", "ETCO2",
    "IV", "IM", "SC", "PO", "PR", "SL", "OD", "OS", "OU", "AU",
    "AD", "AS", "APAP", "NSAID", "PPI", "ARB", "ACE", "BB", "CCB",
    "SSRI", "SNRI", "TCA", "MAOI", "APAP", "DM", "HTN", "HLD",
    "CAD", "PVD", "CKD", "ESRD", "AKI", "COPD", "ASTHMA", "GERD",
    "IBD", "IBS", "NASH", "NAFLD", "HCC", "ALL", "AML", "CLL",
    "CML", "NHL", "Hodgkin", "CML", "MM", "SLE", "RA", "OA",
    "DJD", "GOUT", "RA", "SLE", "MG", "MS", "ALS", "GBS", "TBI",
    "AD", "PD", "HD", "CJD", "SCI", "CA", "N/V", "SOB", "CP",
    "N/V/D", "LOC", "GCS", "HEENT", "CV", "GI", "GU", "MSK",
    "Neuro", "Psych", "Derm", "ENT", "OB", "GYN", "LMP", "EDC",
    "Gest", "NS", "LR", "D5W", "D5NS", "D5LR", "KCl", "MgSO4",
    "CaCl2", "NaHCO3", "ABG", "VBG", "LP", "BM", "GU", "PEG",
    "ICD", "Pacemaker", "AICD", "CABG", "PCI", "TAVR", "TEVAR",
    "EVAR", "PTCA", "ETOH", "IVDU", "TCA", "APAP", "ASA",
    "NYD", "HX", "Sx", "Tx", "Dx", "Rx", "Hx", "FHx", "SHx",
]

# Common clinical terms - diagnoses, procedures, conditions
CLINICAL_TERMS = [
    # Cardiovascular
    "myocardial infarction", "angina pectoris", "arrhythmia",
    "atrial fibrillation", "ventricular fibrillation", "tachycardia",
    "bradycardia", "hypertension", "hypotension", "atherosclerosis",
    "endocarditis", "pericarditis", "myocarditis", "cardiomyopathy",
    "thromboembolism", "thrombophlebitis", "phlebitis", "embolism",
    "stenosis", "regurgitation", "prolapse", "aneurysm", "dissection",
    "ischemia", "infarction", "reperfusion", "hypercholesterolemia",
    "hypertriglyceridemia", "hypoalbuminemia",

    # Respiratory
    "pneumonia", "bronchitis", "bronchiectasis", "emphysema",
    "pneumothorax", "hemothorax", "pleural effusion", "pleurisy",
    "atelectasis", "pulmonary embolism", "pulmonary edema",
    "pulmonary fibrosis", "sarcoidosis", "tuberculosis", "asthma",
    "hypoxia", "hypercapnia", "respiratory failure", "apnea",
    "dyspnea", "hemoptysis", "stridor", "wheezing", "coryza",

    # GI
    "gastroesophageal reflux", "esophagitis", "gastritis", "peptic ulcer",
    "gastroenteritis", "colitis", "ulcerative colitis", "Crohn's disease",
    "diverticulitis", "appendicitis", "cholecystitis", "pancreatitis",
    "hepatitis", "cirrhosis", "cholestasis", "steatosis", "steatohepatitis",
    "peritonitis", "ileus", "intussusception", "volvulus",
    "hematemesis", "melena", "hematochezia", "choledocholithiasis",
    "cholelithiasis", "nephrolithiasis", "sialadenitis",

    # Renal/GU
    "nephritis", "nephrosis", "glomerulonephritis", "pyelonephritis",
    "cystitis", "urethritis", "ureterolithiasis", "hydronephrosis",
    "oliguria", "anuria", "hematuria", "proteinuria", "dysuria",
    "incontinence", "retention", "azoospermia", "oligospermia",

    # Neuro
    "encephalopathy", "encephalitis", "meningitis", "myelitis",
    "neuropathy", "radiculopathy", "myelopathy", "ataxia",
    "dysarthria", "aphasia", "apraxia", "agnosia", "anomia",
    "dysphagia", "dysphonia", "dyskinesia", "myoclonus", "chorea",
    "athetosis", "dystonia", "tremor", "fasciculation", "clonus",
    "nystagmus", "ptosis", "miosis", "mydriasis", "anisocoria",
    "hyperreflexia", "hyporeflexia", "Babinski", "paresthesia",
    "anesthesia", "hyperesthesia", "dysesthesia", "neuralgia",
    "neuritis", "sciatica", "trigeminal", "prosopagnosia",

    # Endocrine
    "hyperthyroidism", "hypothyroidism", "thyrotoxicosis",
    "myxedema", "hyperparathyroidism", "hypoparathyroidism",
    "hypercalcemia", "hypocalcemia", "hyperkalemia", "hypokalemia",
    "hypernatremia", "hyponatremia", "hypomagnesemia",
    "hypermagnesemia", "hypophosphatemia", "hyperphosphatemia",
    "acidosis", "alkalosis", "ketoacidosis", "hypoglycemia",
    "hyperglycemia", "insulinoma", "pheochromocytoma",

    # Hematology
    "anemia", "polycythemia", "thrombocytopenia", "thrombocytosis",
    "leukopenia", "leukocytosis", "neutropenia", "neutrophilia",
    "lymphopenia", "lymphocytosis", "monocytosis", "eosinophilia",
    "basophilia", "pancytopenia", "hemophilia", "thrombophilia",
    "purpura", "petechiae", "ecchymosis", "hematoma", "hemolysis",

    # Infectious disease
    "cellulitis", "abscess", "furuncle", "carbuncle", "impetigo",
    "erysipelas", "necrotizing fasciitis", "osteomyelitis",
    "septic arthritis", "sepsis", "septicemia", "bacteremia",
    "viremia", "fungemia", "parasitemia", "endotoxemia",

    # Dermatology
    "erythema", "urticaria", "pruritus", "eczema", "psoriasis",
    "lichenification", "excoriation", "vesicle", "bulla", "pustule",
    "macule", "papule", "nodule", "plaque", "scale", "crust",
    "erosion", "ulcer", "fissure", "atrophy", "sclerosis",

    # Procedures
    "appendectomy", "cholecystectomy", "herniorrhaphy", "colostomy",
    "ileostomy", "nephrectomy", "hysterectomy", "mastectomy",
    "thyroidectomy", "parathyroidectomy", "adrenalectomy",
    "splenectomy", "pancreatectomy", "esophagectomy", "gastrectomy",
    "colectomy", "proctectomy", "cystectomy", "nephrostomy",
    "ureterostomy", "tracheostomy", "cricothyroidotomy", "thoracotomy",
    "sternotomy", "laparotomy", "celiotomy", "arthroscopy",
    "bronchoscopy", "colonoscopy", "endoscopy", "gastroscopy",
    "sigmoidoscopy", "cystoscopy", "colposcopy", "hysteroscopy",
    "laparoscopy", "thoracoscopy", "mediastinoscopy", "arthroplasty",
    "osteotomy", "craniotomy", "laminectomy", "discectomy",
    "rhizotomy", "neurectomy", "sympathectomy", "vagotomy",
    "angina", "diabetes mellitus", "hyperlipidemia", "osteoarthritis",
]

# Common anatomical terms - frequently used in clinical conversations
ANATOMICAL_TERMS = [
    "epithelium", "endothelium", "mesothelium", "stratum corneum",
    "dermis", "epidermis", "hypodermis", "subcutaneous",
    "fascia", "ligament", "tendon", "aponeurosis", "bursa",
    "meniscus", "cartilage", "periosteum", "endosteum",
    "diaphysis", "epiphysis", "metaphysis", "physis",
    "symphysis", "synovium", "synovia", "sutura", "fontanelle",
    "myocardium", "epicardium", "pericardium", "endocardium",
    "intima", "media", "adventitia", "tunica",
    "parenchyma", "stroma", "septum", "septa", "trabecula",
    "hilum", "hilus", "fissure", "sulcus", "gyrus",
    "cortex", "medulla", "capsule", "lobe", "lobule",
    "acinus", "alveolus", "glomerulus", "nephron", "tubule",
    "ductule", "ductus", "vas deferens", "epididymis",
    "fimbria", "fornix", "mesentery", "omentum", "peritoneum",
    "retroperitoneum", "mesocolon", "haustra", "plicae",
    "rugae", "villi", "microvilli", "cryptae", "pylorus",
    "cardia", "fundus", "antrum", "duodenum", "jejunum",
    "ileum", "cecum", "vermiform", "appendix", "sigmoid",
    "rectum", "anus", "sphincter", "papilla", "ampulla",
    "cholecyst", "choledochus", "pancreas", "islets",
    "acini", "centrilobular", "periportal", "sinusoids",
    "Kupffer", "space of Disse", "canaliculi", "falciform",
    "ligamentum teres", "ligamentum venosum", "porta hepatis",
    "coronary", "circumflex", "interventricular", "interventricular septum",
    "papillary muscle", "chordae tendineae", "leaflet",
    "semilunar", "atrioventricular", "ventricular",
    "sinoatrial", "coronary sinus", "vena cava", "pulmonary trunk",
    "aorta", "carotid", "subclavian", "vertebral", "basilar",
    "circle of Willis", "meninges", "dura mater", "arachnoid",
    "pia mater", "subdural", "subarachnoid", "epidural",
    "ventricles", "foramina", "aqueduct", "choroid plexus",
    "cauda equina", "filum terminale", "conus medullaris",
    "dorsal root", "ventral root", "ganglion", "plexus",
    "phrenic", "vagus", "recurrent laryngeal", "trigeminal",
    "facial", "vestibulocochlear", "glossopharyngeal", "hypoglossal",
    "accessory", "oculomotor", "trochlear", "abducens",
]


def get_all_terms():
    """Return all terms with their category."""
    terms = []
    for t in TOP_DRUGS:
        terms.append({"text": t, "category": "drug"})
    for t in MEDICAL_ACRONYMS:
        terms.append({"text": t, "category": "acronym"})
    for t in CLINICAL_TERMS:
        terms.append({"text": t, "category": "clinical"})
    for t in ANATOMICAL_TERMS:
        terms.append({"text": t, "category": "anatomical"})
    # Deduplicate by text, preserving first occurrence
    seen = set()
    unique = []
    for t in terms:
        key = t["text"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


if __name__ == "__main__":
    all_terms = get_all_terms()
    cats = {}
    for t in all_terms:
        cats[t["category"]] = cats.get(t["category"], 0) + 1
    print(f"Total unique terms: {len(all_terms)}")
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")
