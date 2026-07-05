#!/usr/bin/env python3
import re

CATEGORY_ALIASES = {
    "fashion": [
        "fashion", "boutique", "clothing", "dress", "kameez",
        "saree", "hijab", "garments", "wear", "apparel",
        "panjabi", "salwar", "kurti", "orna",
    ],
    "jewelry": [
        "jewelry", "jewellery", "gold", "silver", "ornament",
        "necklace", "ring", "bracelet", "earring", "gahna",
    ],
    "skincare": [
        "skincare", "skin care", "serum", "moisturizer",
        "sunscreen", "toner", "face wash", "cleanser",
        "derma", "glow", "whitening",
    ],
    "baby": [
        "baby", "kids", "children", "toddler", "infant",
        "maternity", "newborn", "toy", "diaper",
    ],
    "home": [
        "home", "kitchen", "cookware", "furniture", "decor",
        "interior", "household", "homeware", "bedding",
        "curtain", "organizer",
    ],
    "restaurant": [
        "restaurant", "cafe", "food", "dining", "bakery", "grill", "biryani",
        "pizza", "burger", "kebab", "curry", "buffet", "fast food", "coffee shop",
        "tea", "juice", "confectionery", "sweets", "catering", "meal", "kitchen",
        "tiffin", "snacks", "dhaba", "hotel & restaurant",
    ],
    "beauty": [
        "beauty", "salon", "parlor", "parlour", "spa", "makeup", "make-up",
        "make over", "makeover", "nail", "hair", "barber", "grooming",
        "skincare", "skin care", "facial", "bridal", "massage", "wellness",
        "cosmetic", "cosmetics", "beauty parlor", "beauty salon", "beauty shop",
    ],
    "education": [
        "education", "school", "college", "university", "coaching", "tutorial",
        "training", "academy", "institute", "learning", "madrasa", "kindergarten",
        "preschool", "nursery", "tuition", "class", "lesson", "course",
        "language", "computer training", "skill development", "vocational",
    ],
    "healthcare": [
        "healthcare", "hospital", "clinic", "diagnostic", "medical",
        "doctor", "dentist", "dental", "eye", "ent", "physiotherapy", "laboratory", "lab",
        "health", "nursing", "care", "surgery", "orthopedic",
        "cardiology", "dermatology", "gynecology", "child", "diabetes",
        "blood", "x-ray", "ultrasound", "optical",
    ],
    "pharmacy": [
        "pharmacy", "drug", "drug store", "pharmaceutical", "chemist",
        "medicines", "wellness store", "health shop",
    ],
    "fitness": [
        "fitness", "gym", "yoga", "zumba", "workout",
        "crossfit", "martial arts", "boxing", "dance studio",
        "health club", "fitness center", "pilates", "aerobics",
    ],
    "automotive": [
        "auto", "automobile", "automotive", "car", "vehicle",
        "mechanic", "garage", "workshop", "car wash", "towing",
        "service center", "spare parts", "tire", "tyre",
        "engine", "body shop", "paint shop", "petrol pump",
        "fuel station", "electric vehicle", "ev charging",
    ],
    "manufacturing": [
        "manufacturing", "manufacturer", "factory", "industry", "industrial",
        "production", "processing", "fabrication", "engineering", "workshop",
        "foundry", "printing", "packaging", "textile", "garment factory",
        "pharmaceutical", "chemical", "plastic", "metal", "steel", "cement",
        "food processing", "beverage", "furniture factory",
    ],
    "agriculture": [
        "agriculture", "farm", "farming", "agro", "dairy", "poultry", "hatchery",
        "fishery", "fish", "livestock", "cattle", "feed", "seed", "fertilizer",
        "nursery", "garden", "plantation", "crop", "organic", "agro products",
    ],
    "hotel": [
        "hotel", "resort", "motel", "inn", "guest house", "guesthouse",
        "lodging", "accommodation", "rest house", "hostel", "holiday",
        "vacation", "tourist", "travel lodge",
    ],
    "realestate": [
        "real estate", "realestate", "property", "apartment", "flat",
        "land", "plot", "developer", "builder", "construction", "housing",
        "building", "realtor", "broker", "rental", "leasing",
    ],
    "services": [
        "service", "electrician", "plumber", "carpenter", "painter",
        "repair", "maintenance", "cleaning", "laundry", "dry cleaning",
        "tailor", "alteration", "photography", "event", "decoration",
        "rental", "logistics", "delivery", "courier", "transport",
        "travel", "agency", "consultant", "consultancy", "it services",
        "software", "digital marketing", "graphic design", "web development",
        "security", "interior design", "architect", "engineering services",
    ],
    "retail": [
        "retail", "store", "shop", "footwear", "electronics", "gadget", "mobile",
        "computer", "accessories", "gift", "supermarket", "grocery",
        "department store", "shopping", "market", "trading", "wholesale",
        "books", "stationery", "sports", "optical", "watch", "perfume",
    ],
    "cto_it_director": [
        "cto", "chief technology officer", "it director", "head of it",
        "head of technology", "vp technology", "vp engineering",
        "chief digital officer", "technology lead", "digital transformation",
        "it manager", "software director"
    ],
    "school_admin": [
        "principal", "school director", "college director", "head teacher",
        "academic director", "campus director", "education director",
        "school administrator", "college administrator", "university registrar"
    ],
    "clinic_admin": [
        "clinic manager", "hospital administrator", "medical director",
        "diagnostic manager", "lab manager", "healthcare manager",
        "clinic owner", "hospital owner", "medical admin"
    ],
    "operations_manager": [
        "operations manager", "factory manager", "plant manager",
        "production manager", "supply chain manager", "logistics manager",
        "manufacturing manager", "general manager", "md", "managing director"
    ],
    "business_owner": [
        "founder", "co-founder", "owner", "proprietor", "entrepreneur",
        "managing partner", "business owner", "self-employed"
    ],
    "footwear": [
        "shoe", "shoes", "footwear", "sandal", "sneaker", "boot",
        "slipper", "loafer", "heel", "chappal", "joota", "জুতা",
    ],
    "baby_kids": [
        "baby", "kids", "children", "toddler", "infant", "maternity",
        "newborn", "toy", "diaper", "baby shop", "kids store",
    ],
    "fitness": [
        "gym", "fitness", "yoga", "workout", "exercise", "supplement",
        "protein", "health club", "wellness center", "zumba",
    ],
    "real_estate": [
        "real estate", "property", "apartment", "flat", "land",
        "housing", "plot", "commercial space", "office space", "rental",
    ],
    "automotive": [
        "car", "automobile", "vehicle", "bike", "motorcycle", "workshop",
        "garage", "mechanic", "auto parts", "tire", "car accessories",
    ],
    "agriculture": [
        "farm", "agriculture", "agro", "seeds", "fertilizer", "pesticide",
        "crop", "livestock", "poultry", "dairy", "harvest",
    ],
    "hotel_hospitality": [
        "hotel", "resort", "motel", "guest house", "hostel", "lodge",
        "inn", "accommodation", "booking", "hospitality",
    ],
}

TROJAN_HORSE_MAP = {
    "fashion": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "jewelry": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "skincare": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "baby": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "home": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "restaurant": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "beauty": {"product": "ExecMate", "entry": "Appointment Management", "pain": "Missed bookings & manual scheduling"},
    "retail": {"product": "ExecERP", "entry": "Inventory Module", "pain": "Stock theft & inaccurate tracking"},
    "education": {"product": "Smart Campus", "entry": "Admissions Module", "pain": "Enrollment chaos & lead loss"},
    "healthcare": {"product": "MediLab", "entry": "Lab Management", "pain": "Slow report delivery & manual errors"},
    "pharmacy": {"product": "MediERP", "entry": "Inventory Tracking", "pain": "Expiry waste & prescription errors"},
    "fitness": {"product": "ExecMate", "entry": "Member Management", "pain": "No-show members & billing headaches"},
    "automotive": {"product": "ExecERP", "entry": "Job Card Management", "pain": "Lost service history & parts mismanagement"},
    "manufacturing": {"product": "ExecERP", "entry": "Production Planning", "pain": "Wasted raw materials & downtime"},
    "agriculture": {"product": "CattleSync", "entry": "Farm Monitoring", "pain": "Crop disease & yield uncertainty"},
    "hotel": {"product": "QueueMaster 360", "entry": "Booking Management", "pain": "Double bookings & guest confusion"},
    "realestate": {"product": "ExecCRM", "entry": "Lead Follow-up", "pain": "Cold leads lost in the shuffle"},
    "services": {"product": "DeskAgent", "entry": "Job Scheduling", "pain": "Missed appointments & service delays"},
    "general": {"product": "ExecMate", "entry": "Business Automation", "pain": "Daily operations chaos"},
}


def normalize(s):
    return re.sub(r"[^a-z0-9\s]", "", s.lower()).strip()


def classify_category(category):
    normalized = normalize(category)
    if not normalized:
        return "general"
    for canonical, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', normalized):
                return canonical
    return "general"


def detect_trojan_horse(business_name, category):
    canonical = classify_category(category)
    mapped = TROJAN_HORSE_MAP.get(canonical)
    if mapped:
        return mapped

    text = f"{business_name} {category}".lower()
    for canonical_name, info in TROJAN_HORSE_MAP.items():
        if canonical_name in text:
            return info
    return None


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    return s.strip("_")


CANONICAL_DISPLAY_NAMES = {
    "fashion": "fashion boutique",
    "jewelry": "jewelry store",
    "skincare": "skincare brand",
    "baby": "baby products store",
    "home": "home decor store",
    "restaurant": "restaurant",
    "beauty": "beauty salon",
    "retail": "retail store",
    "education": "educational institution",
    "healthcare": "healthcare provider",
    "pharmacy": "pharmacy",
    "fitness": "fitness center",
    "automotive": "auto service center",
    "manufacturing": "manufacturer",
    "agriculture": "agricultural business",
    "hotel": "hotel",
    "realestate": "real estate business",
    "services": "service provider",
    "general": "business",
}


def get_display_name(canonical: str) -> str:
    """Return a human-readable category display name."""
    return CANONICAL_DISPLAY_NAMES.get(canonical, "business")


def canonical_icon(canonical: str) -> str:
    """Return an emoji icon for a canonical category."""
    icons = {
        "fashion": "\U0001F455",
        "jewelry": "\U0001F48D",
        "skincare": "\U0001F9F4",
        "baby": "\U0001F476",
        "home": "\U0001F3E0",
        "restaurant": "\U0001F37D\uFE0F",
        "beauty": "\U0001F487",
        "retail": "\U0001F6CD\uFE0F",
        "education": "\U0001F4DA",
        "healthcare": "\U0001FA7A",
        "pharmacy": "\U0001F48A",
        "fitness": "\U0001F4AA",
        "automotive": "\U0001F527",
        "manufacturing": "\U0001F3ED",
        "agriculture": "\U0001F33E",
        "hotel": "\U0001F3E8",
        "realestate": "\U0001F3E0",
        "services": "\u2B50",
        "general": "\u2B50",
    }
    return icons.get(canonical, "\u2B50")
