#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_gen_outreach.py — Shopify 2026 e-commerce demo generator.

Generates multi-page (index, products, order) Shopify-style websites
with per-category design tokens, Bengali/English toggle, WhatsApp ordering.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple, Optional

# ── Category Products ────────────────────────────────────────────────
CATEGORY_PRODUCTS: Dict[str, List[str]] = {
    "fashion": ["Kameez Collection", "Saree Set", "Hijab Pack", "Panjabi Set", "Salwar Suit", "Silk Dupatta", "Cotton Kurti", "Designer Lehenga", "Boys Kurta Set", "Girls Frock"],
    "jewelry": ["Necklace Set", "Earring Pair", "Bangle Set", "Ring", "Anklet", "Mangalsutra", "Nose Pin", "Pendant Set", "Toe Ring", "Cufflinks"],
    "skincare": ["Vitamin C Serum", "Sunscreen SPF50", "Face Wash", "Toner Mist", "Night Cream", "Eye Cream", "Sheet Mask Pack", "Lip Balm SPF", "Body Lotion", "Face Scrub"],
    "baby": ["Baby Bodysuit", "Feeding Bottle", "Diaper Pack", "Toy Set", "Baby Skincare Set", "Baby Blanket", "Walker", "Baby Shampoo", "Teether Ring", "Baby Wipes"],
    "home": ["Ceramic Dinner Set", "Storage Organizer", "Bedsheet Set", "Cushion Cover", "Kitchen Rack", "Airtight Container", "Decorative Vase", "Wall Clock", "Fridge Organizer", "Carpet Runner"],
    "restaurant": ["Chef Special Platter", "Family Combo Meal", "Signature Dish", "Dessert Box", "Party Platter", "Grilled Chicken", "Beef Steak", "Seafood Platter", "Pasta Bowl", "Healthy Salad"],
    "beauty": ["Matte Lipstick Set", "Vitamin C Serum", "Gel Eyeliner", "Face Cream", "Nail Kit", "Toner Mist", "Makeup Brush Set", "Setting Spray", "Lip Gloss", "Concealer Palette"],
    "retail": ["Premium Gift Box", "Electronics Bundle", "Home Combo", "Fashion Set", "Care Package", "Smart Gadget", "Organic Hamper", "Starter Kit", "Office Pack", "Travel Set"],
    "education": ["Course Bundle", "Study Kit", "Lab Package", "Workshop Pass", "Certification Pack", "E-Book Set", "Practice Test", "Video Course", "Mentoring Session", "Flash Card Pack"],
    "healthcare": ["Health Checkup", "Wellness Package", "Medicine Kit", "Care Bundle", "Diagnostic Set", "BP Monitor", "Glucose Meter", "First Aid Box", "Vitamin Pack", "Mask Pack"],
    "pharmacy": ["Medicine Combo", "Wellness Kit", "Supplement Pack", "First Aid Set", "Health Bundle", "Cough Syrup", "Pain Relief Gel", "Multivitamin", "Antiseptic Pack", "Bandage Set"],
    "fitness": ["Gym Combo", "Protein Pack", "Training Set", "Fitness Gear", "Wellness Kit", "Yoga Mat", "Resistance Band", "Dumbbell Set", "Jump Rope", "Water Bottle"],
    "automotive": ["Service Package", "Spare Parts Kit", "Maintenance Set", "Car Care Combo", "Tire Set", "Car Freshener", "Seat Cover", "Dash Cam", "Car Charger", "Polish Kit"],
    "manufacturing": ["Production Kit", "Tool Set", "Safety Pack", "Component Bundle", "Test Package", "Work Gloves", "Safety Goggles", "Toolbox", "Cleaning Kit", "Label Pack"],
    "agriculture": ["Seed Pack", "Fertilizer Set", "Tool Combo", "Crop Care Kit", "Harvest Pack", "Pesticide Set", "Soil Tester", "Garden Gloves", "Watering Kit", "Plant Pot Set"],
    "hotel": ["Stay Package", "Dining Voucher", "Room Combo", "Spa Set", "Weekend Pack", "Breakfast Combo", "Pool Access", "Suite Upgrade", "Candlelight Dinner", "Late Checkout"],
    "realestate": ["Property Pack", "Inspection Kit", "Legal Set", "Moving Package", "Consultation Voucher", "Valuation Report", "Area Guide", "Mortgage Pack", "Rental Kit", "Design Plan"],
    "services": ["Service Plan", "Maintenance Pack", "Checkup Set", "Support Plan", "Annual Care", "Consultation", "Express Service", "Premium Support", "Family Plan", "Business Pack"],
    "general": ["Premium Item", "Combo Pack", "Value Set", "Gift Box", "Care Package", "Starter Bundle", "Family Pack", "Exclusive Item", "Budget Saver", "Mega Deal"],
}

CATEGORY_PRODUCT_DESCS: Dict[str, List[str]] = {
    "fashion": ["Trendy & comfortable", "Elegant traditional", "Premium quality", "Stylish classic", "Beautiful handcrafted", "Luxury silk finish", "Soft & breathable", "Party wear special", "Smart casual", "Cute & colorful"],
    "jewelry": ["Exquisite design", "Pure elegance", "Handcrafted beauty", "Timeless classic", "Stunning finish", "Sacred elegance", "Delicate touch", "Everyday chic", "Traditional touch", "Modern style"],
    "skincare": ["Natural glow", "SPF protection", "Deep cleansing", "Instant hydration", "Brightening formula", "Anti-aging", "Hydrating glow", "Daily protection", "All-day moisture", "Gentle exfoliation"],
    "baby": ["Soft & safe", "BPA-free", "Ultra absorbent", "Educational fun", "Gentle formula", "Cozy warmth", "Supports walking", "Tear-free wash", "Soothing relief", "Gentle clean"],
    "home": ["Premium ceramic", "Smart storage", "Luxury cotton", "Designer print", "Space saving", "Airtight fresh", "Elegant decor", "Modern design", "Organized fridge", "Soft texture"],
    "restaurant": ["Chef's special", "Best value", "Signature taste", "Sweet delight", "Party favorite", "Juicy & tender", "Premium cut", "Fresh catch", "Italian classic", "Light & fresh"],
    "beauty": ["12 trendy shades", "Brightening", "Smudge-proof", "24hr moisture", "Complete kit", "Natural mist", "Pro quality", "Long-lasting", "Shiny finish", "Flawless coverage"],
    "retail": ["Premium curated", "Latest tech", "Best value", "Trendy styles", "Essential care", "Smart choice", "Organic selection", "Perfect start", "Office ready", "Travel ready"],
    "education": ["Complete learning", "All essentials", "Hands-on tools", "Expert led", "Career boost", "Digital library", "Test your skills", "Watch & learn", "One-on-one", "Learn anywhere"],
    "healthcare": ["Comprehensive", "Complete care", "Essential meds", "Total wellness", "Accurate diagnosis", "Easy monitoring", "Track glucose", "Emergency ready", "Daily nutrition", "Essential protection"],
    "pharmacy": ["Essential care", "Daily wellness", "Natural boost", "Emergency ready", "Complete health", "Fast relief", "Targeted care", "Daily essential", "Wound care", "Injury prep"],
    "fitness": ["Full workout", "Muscle fuel", "Complete training", "Pro gear", "Total health", "Core strength", "Flexibility", "Home gym", "Cardio boost", "Stay hydrated"],
    "automotive": ["Full service", "Genuine parts", "Complete care", "Premium wash", "Safe ride", "Fresh drive", "Comfort ride", "Drive safe", "Power on", "Showroom shine"],
    "manufacturing": ["Complete setup", "Pro grade", "Safety first", "Quality parts", "Tested quality", "Heavy duty", "Clear vision", "Organized pro", "Workplace hygiene", "Easy labeling"],
    "agriculture": ["High yield", "Rich nutrients", "Essential tools", "Crop health", "Premium fresh", "Pest control", "Smart farming", "Garden ready", "Easy irrigation", "Green decor"],
    "hotel": ["Luxury stay", "Fine dining", "Premium room", "Relaxation", "Weekend escape", "Morning feast", "Swim & relax", "Extra comfort", "Romantic evening", "Sleep in"],
    "realestate": ["Complete guide", "Thorough check", "All documents", "Smooth move", "Expert advice", "Market value", "Local insights", "Finance help", "Rental ready", "Dream home"],
    "services": ["Complete care", "Peace of mind", "Regular check", "Full support", "Year round", "Expert advice", "Priority service", "Premium care", "Family value", "Corporate plan"],
    "general": ["Premium quality", "Best value", "Great deal", "Perfect gift", "Essential choice", "Complete bundle", "Family size", "Limited edition", "Budget friendly", "Mega value"],
}

CATEGORY_PRODUCT_PRICES: Dict[str, List[str]] = {
    "fashion": ["1299", "2499", "899", "1599", "1899", "899", "799", "4999", "1299", "999"],
    "jewelry": ["2999", "1499", "2499", "3999", "999", "1999", "399", "1599", "299", "699"],
    "skincare": ["690", "850", "450", "590", "780", "650", "350", "290", "550", "420"],
    "baby": ["599", "349", "499", "899", "450", "699", "1299", "299", "199", "249"],
    "home": ["1599", "899", "1299", "499", "799", "599", "699", "899", "599", "1499"],
    "restaurant": ["599", "999", "749", "499", "1299", "899", "1499", "1599", "699", "499"],
    "beauty": ["850", "690", "350", "590", "450", "295", "699", "499", "399", "599"],
    "retail": ["1499", "2499", "999", "1299", "799", "1999", "1499", "899", "999", "1299"],
    "education": ["2999", "1499", "2499", "1999", "3999", "499", "999", "1999", "2499", "399"],
    "healthcare": ["2999", "1999", "999", "1499", "2499", "1499", "1299", "599", "799", "199"],
    "pharmacy": ["599", "899", "1299", "499", "1999", "120", "250", "499", "150", "199"],
    "fitness": ["1499", "2499", "1799", "2999", "999", "899", "499", "1999", "299", "399"],
    "automotive": ["999", "1499", "1999", "799", "2499", "199", "999", "2999", "499", "599"],
    "manufacturing": ["4999", "2999", "1499", "3999", "1999", "299", "399", "999", "499", "199"],
    "agriculture": ["499", "899", "1499", "599", "1299", "699", "999", "299", "599", "799"],
    "hotel": ["4999", "1999", "3499", "2999", "5999", "999", "799", "3999", "2499", "1499"],
    "realestate": ["999", "1499", "1999", "2499", "2999", "1499", "499", "1999", "999", "2999"],
    "services": ["999", "1499", "1999", "2499", "2999", "999", "1999", "2999", "1499", "3999"],
    "general": ["999", "1499", "1999", "2499", "2999", "999", "1499", "1999", "499", "2999"],
}

CATEGORY_PRODUCT_SUBCATS: Dict[str, List[str]] = {
    "fashion": ["Traditional", "Traditional", "Casual", "Traditional", "Traditional", "Casual", "Casual", "Traditional", "Kids", "Kids"],
    "jewelry": ["Neck & Ear", "Neck & Ear", "Bracelets", "Bracelets", "Bracelets", "Bracelets", "Nose & Toe", "Neck & Ear", "Nose & Toe", "Neck & Ear"],
    "skincare": ["Treatments", "Protection", "Cleansers", "Cleansers", "Treatments", "Treatments", "Treatments", "Protection", "Protection", "Cleansers"],
    "baby": ["Clothing", "Feeding", "Care", "Play", "Feeding", "Clothing", "Play", "Feeding", "Play", "Care"],
    "home": ["Dining & Kitchen", "Storage & Bedding", "Storage & Bedding", "Decor", "Dining & Kitchen", "Storage & Bedding", "Decor", "Decor", "Dining & Kitchen", "Decor"],
    "restaurant": ["Chef's Pick", "Combos", "Chef's Pick", "Combos", "Combos", "Chef's Pick", "Premium", "Premium", "Mains", "Mains"],
    "beauty": ["Lips", "Skincare", "Face", "Face", "Tools", "Skincare", "Tools", "Face", "Lips", "Face"],
    "retail": ["Gift & Home", "Electronics", "Gift & Home", "Fashion", "Health & Food", "Electronics", "Health & Food", "Essentials", "Essentials", "Fashion"],
    "education": ["Courses & Cert", "Materials & Tools", "Materials & Tools", "Courses & Cert", "Courses & Cert", "Digital & Tests", "Digital & Tests", "Digital & Tests", "Courses & Cert", "Materials & Tools"],
    "healthcare": ["Checkups & Wellness", "Checkups & Wellness", "Devices & Meds", "Checkups & Wellness", "Checkups & Wellness", "Devices & Meds", "Devices & Meds", "Devices & Meds", "Supplements & Protection", "Supplements & Protection"],
    "pharmacy": ["Combos & Wellness", "Combos & Wellness", "Supplements", "First Aid", "Combos & Wellness", "OTC & Relief", "OTC & Relief", "Supplements", "First Aid", "First Aid"],
    "fitness": ["Equipment & Training", "Wellness & Acc", "Equipment & Training", "Equipment & Training", "Wellness & Acc", "Equipment & Training", "Equipment & Training", "Equipment & Training", "Equipment & Training", "Wellness & Acc"],
    "automotive": ["Service & Care", "Parts", "Service & Care", "Service & Care", "Parts", "Accessories & Interior", "Accessories & Interior", "Electronics", "Electronics", "Accessories & Interior"],
    "manufacturing": ["Setup & Comp", "Tools & Supplies", "Safety", "Setup & Comp", "Testing", "Safety", "Safety", "Tools & Supplies", "Tools & Supplies", "Testing"],
    "agriculture": ["Seeds & Fertilizers", "Seeds & Fertilizers", "Tools & Planters", "Crop Care", "Crop Care", "Seeds & Fertilizers", "Tools & Planters", "Tools & Planters", "Crop Care", "Tools & Planters"],
    "hotel": ["Stays & Rooms", "Dining", "Stays & Rooms", "Packages & More", "Packages & More", "Dining", "Packages & More", "Stays & Rooms", "Dining", "Packages & More"],
    "realestate": ["Property & Valuation", "Inspection & Moving", "Legal & Finance", "Inspection & Moving", "Consulting & Design", "Property & Valuation", "Consulting & Design", "Legal & Finance", "Legal & Finance", "Consulting & Design"],
    "services": ["Plans & Annual", "Maintenance & Checkups", "Maintenance & Checkups", "Support", "Plans & Annual", "Premium & Corp", "Support", "Premium & Corp", "Plans & Annual", "Premium & Corp"],
    "general": ["Premium & Exclusive", "Combo & Family", "Value & Budget", "Gift & Care", "Gift & Care", "Combo & Family", "Combo & Family", "Premium & Exclusive", "Value & Budget", "Combo & Family"],
}

CATEGORY_BENGALI_NAMES: Dict[str, str] = {
    "fashion": "ফ্যাশন",
    "jewelry": "জুয়েলারি",
    "skincare": "স্কিনকেয়ার",
    "baby": "বেবি প্রোডাক্ট",
    "home": "হোম এন্ড কিচেন",
    "restaurant": "রেস্টুরেন্ট",
    "beauty": "বিউটি",
    "retail": "রিটেইল",
    "education": "এডুকেশন",
    "healthcare": "হেলথকেয়ার",
    "pharmacy": "ফার্মেসি",
    "fitness": "ফিটনেস",
    "automotive": "অটোমোটিভ",
    "manufacturing": "ম্যানুফ্যাকচারিং",
    "agriculture": "এগ্রিকালচার",
    "hotel": "হোটেল",
    "realestate": "রিয়েল এস্টেট",
    "services": "সার্ভিস",
    "general": "জেনারেল",
}

CATEGORY_STORE_NAMES: Dict[str, str] = {
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
    "general": "store",
}

CATEGORY_STAT_ITEMS: Dict[str, List[Tuple[str, str, str]]] = {
    "fashion": [("👗", "500+", "Styles Available"), ("⭐", "4.8", "Customer Rating"), ("🚚", "1000+", "Orders Delivered"), ("🏙️", "30+", "Cities Served")],
    "jewelry": [("💍", "300+", "Designs"), ("⭐", "4.9", "Rating"), ("📦", "500+", "Delivered"), ("🏪", "2", "Showrooms")],
    "skincare": [("🧴", "50+", "Products"), ("⭐", "4.7", "Rating"), ("📦", "2000+", "Sold"), ("🧪", "100%", "Original")],
    "baby": [("👶", "200+", "Products"), ("⭐", "4.8", "Rating"), ("📦", "3000+", "Delivered"), ("✅", "Safe", "Materials")],
    "home": [("🏠", "300+", "Products"), ("⭐", "4.7", "Rating"), ("📦", "1500+", "Delivered"), ("🏪", "1", "Showroom")],
    "restaurant": [("🍽️", "200+", "Menu Items"), ("⭐", "4.8", "Rating"), ("👥", "5000+", "Happy Customers"), ("🏆", "5+", "Awards")],
    "beauty": [("💇", "5000+", "Happy Clients"), ("⭐", "4.8", "Rating"), ("📦", "10000+", "Orders"), ("🏆", "3+", "Awards")],
    "retail": [("📦", "5000+", "Products"), ("⭐", "4.7", "Rating"), ("🚚", "10000+", "Orders"), ("🏪", "3", "Stores")],
    "education": [("📚", "50+", "Courses"), ("⭐", "4.8", "Rating"), ("👨‍🎓", "2000+", "Students"), ("🏆", "10+", "Years")],
    "healthcare": [("🏥", "20+", "Years"), ("⭐", "4.9", "Rating"), ("👥", "10000+", "Patients"), ("🏆", "Trusted", "Provider")],
    "pharmacy": [("💊", "1000+", "Medicines"), ("⭐", "4.8", "Rating"), ("🚚", "5000+", "Deliveries"), ("✅", "100%", "Genuine")],
    "fitness": [("💪", "500+", "Members"), ("⭐", "4.8", "Rating"), ("🏋️", "50+", "Programs"), ("🏆", "5+", "Years")],
    "automotive": [("🔧", "5000+", "Cars Serviced"), ("⭐", "4.7", "Rating"), ("🛠️", "20+", "Years"), ("🏆", "Certified", "Techs")],
    "manufacturing": [("🏭", "25+", "Years"), ("⭐", "4.8", "Rating"), ("📦", "10000+", "Units"), ("✅", "ISO", "Certified")],
    "agriculture": [("🌾", "30+", "Years"), ("⭐", "4.7", "Rating"), ("🚜", "200+", "Farmers"), ("✅", "Organic", "Certified")],
    "hotel": [("🛏️", "50+", "Rooms"), ("⭐", "4.7", "Rating"), ("👥", "10000+", "Guests"), ("🏆", "4-Star", "Rating")],
    "realestate": [("🏠", "500+", "Properties"), ("⭐", "4.8", "Rating"), ("👥", "2000+", "Clients"), ("🤝", "10+", "Years")],
    "services": [("⭐", "4.8", "Rating"), ("👥", "2000+", "Clients"), ("🔧", "5000+", "Jobs Done"), ("🏆", "10+", "Years")],
    "general": [("⭐", "4.8", "Rating"), ("👥", "1000+", "Clients"), ("📦", "5000+", "Delivered"), ("🏆", "5+", "Years")],
}

CATEGORY_TRUST_ITEMS: Dict[str, List[Tuple[str, str]]] = {
    "fashion": [("🚚", "Fast Delivery"), ("💳", "Cash on Delivery"), ("✅", "100% Original"), ("🔄", "Easy Exchange")],
    "jewelry": [("🚚", "Fast Delivery"), ("💳", "Cash on Delivery"), ("✅", "Certified"), ("🎁", "Gift Wrapped")],
    "skincare": [("🚚", "Fast Delivery"), ("💳", "COD Available"), ("✅", "Dermatologist Tested"), ("🧪", "Lab Certified")],
    "baby": [("🚚", "Fast Delivery"), ("💳", "COD Available"), ("✅", "Baby Safe"), ("🔄", "Easy Return")],
    "home": [("🚚", "Fast Delivery"), ("💳", "COD Available"), ("✅", "Premium Quality"), ("🔄", "Easy Return")],
    "restaurant": [("🚚", "Fast Delivery"), ("💳", "Cash on Delivery"), ("✅", "Fresh Food"), ("⭐", "Hygienic")],
    "beauty": [("🚚", "Fast Delivery"), ("💳", "Cash on Delivery"), ("✅", "100% Original"), ("🔄", "Easy Exchange")],
    "retail": [("🚚", "Fast Delivery"), ("💳", "Cash on Delivery"), ("✅", "Quality Assured"), ("🔄", "Easy Return")],
    "education": [("📚", "Expert Faculty"), ("💻", "Modern Labs"), ("🏆", "Certified"), ("🤝", "Career Support")],
    "healthcare": [("🏥", "Expert Doctors"), ("🔬", "Modern Lab"), ("💊", "Pharmacy"), ("🤝", "24/7 Care")],
    "pharmacy": [("🚚", "Free Delivery"), ("💳", "COD Available"), ("✅", "100% Genuine"), ("🔬", "Pharmacist Advice")],
    "fitness": [("💪", "Expert Trainers"), ("🏋️", "Modern Equipment"), ("🧘", "Group Classes"), ("🥗", "Nutrition Guide")],
    "automotive": [("🔧", "Expert Mechanics"), ("🛡️", "Service Warranty"), ("✅", "Quality Parts"), ("🚗", "Free Pickup")],
    "manufacturing": [("🏭", "Modern Facility"), ("✅", "QC Tested"), ("📦", "Bulk Orders"), ("🚚", "On-Time")],
    "agriculture": [("🌾", "Farm Fresh"), ("✅", "Quality Tested"), ("🚜", "Bulk Supply"), ("🌱", "Sustainable")],
    "hotel": [("🛏️", "Comfort Rooms"), ("🍳", "Free Breakfast"), ("📶", "Free WiFi"), ("🤝", "24/7 Service")],
    "realestate": [("🏠", "Prime Properties"), ("✅", "Verified Listings"), ("🤝", "Expert Advice"), ("📋", "Paperwork Help")],
    "services": [("🔧", "Expert Team"), ("✅", "Quality Work"), ("🤝", "Satisfaction"), ("🚀", "Fast Service")],
    "general": [("⭐", "Quality Service"), ("🤝", "Trusted"), ("🚚", "Fast"), ("💳", "COD")],
}

CATEGORY_STORY_TITLE: Dict[str, str] = {
    "fashion": "Our Fashion Story",
    "jewelry": "Our Craftsmanship Story",
    "skincare": "Our Beauty Philosophy",
    "baby": "Our Care Promise",
    "home": "Our Home Vision",
    "restaurant": "Our Culinary Journey",
    "beauty": "Our Beauty Philosophy",
    "retail": "Our Retail Story",
    "education": "Our Educational Mission",
    "healthcare": "Our Healthcare Promise",
    "pharmacy": "Our Care Commitment",
    "fitness": "Our Fitness Mission",
    "automotive": "Our Service Story",
    "manufacturing": "Our Manufacturing Legacy",
    "agriculture": "Our Farming Heritage",
    "hotel": "Our Hospitality Promise",
    "realestate": "Our Real Estate Story",
    "services": "Our Service Commitment",
    "general": "Our Story",
}

CATEGORY_STORY_TEXT: Dict[str, str] = {
    "fashion": "We bring you the latest trends with quality fabrics and perfect craftsmanship. From traditional wear to modern styles, every piece is selected to help you express your unique identity.",
    "jewelry": "Each piece in our collection is crafted with precision and passion. We source the finest materials to create jewelry that celebrates life's precious moments.",
    "skincare": "We believe healthy skin is beautiful skin. Our products are formulated with care, using ingredients that nourish and protect. Glow naturally with our science-backed skincare.",
    "baby": "Your little one deserves the best. We carefully select baby products that meet the highest safety standards. Because nothing matters more than your child's wellbeing.",
    "home": "Transform your living space with our curated home collection. From kitchen essentials to decor accents, we bring quality and style to every corner of your home.",
    "restaurant": "Every dish we serve tells a story of tradition and passion. Using the freshest ingredients and time-honored recipes, we create dining experiences that bring people together.",
    "beauty": "We believe every person deserves to look and feel their best. Our premium beauty products are carefully selected to help you express your unique beauty with confidence.",
    "retail": "Quality products at fair prices — that's our promise. We carefully curate every item to ensure you get the best value without compromising on quality.",
    "education": "Learning transforms lives. We provide quality education with modern facilities and expert faculty to prepare students for real-world success.",
    "healthcare": "Your health is our priority. We combine modern medical technology with compassionate care to provide the best healthcare experience for every patient.",
    "pharmacy": "Your health partner, always available. We stock genuine medicines and provide expert guidance to help you and your family stay healthy.",
    "fitness": "Transform your body, elevate your life. Our modern facility and expert trainers help you achieve your fitness goals in a supportive community.",
    "automotive": "Expert care for your vehicle. Our certified technicians use modern diagnostic tools to keep your car running smoothly and safely.",
    "manufacturing": "Built with precision, delivered with pride. Our modern facility combines quality materials with skilled craftsmanship to produce excellence.",
    "agriculture": "Growing quality, harvesting trust. We bring fresh, sustainably grown produce from our farms to your table with care at every step.",
    "hotel": "Where comfort meets genuine care. Every stay is designed to make you feel at home with thoughtful amenities and warm hospitality.",
    "realestate": "Find the space where your story begins. We help you navigate the property market with expertise, integrity, and personalized service.",
    "services": "Professional service, personal touch. Our skilled team delivers quality workmanship with transparent pricing and genuine care.",
    "general": "Committed to excellence. We are dedicated to delivering exceptional quality and service to every customer, every time.",
}

CATEGORY_ABOUT_TITLE_BN: Dict[str, str] = {
    "fashion": "আমাদের ফ্যাশন স্টোরি",
    "jewelry": "আমাদের ক্রাফটসম্যানশিপ",
    "skincare": "আমাদের বিউটি ফিলোসফি",
    "baby": "আমাদের কেয়ার পledge",
    "home": "আমাদের হোম ভিশন",
    "restaurant": "আমাদের রান্নার যাত্রা",
    "beauty": "আমাদের সৌন্দর্য দর্শন",
    "retail": "আমাদের খুচরা গল্প",
    "education": "আমাদের শিক্ষা লক্ষ্য",
    "healthcare": "আমাদের স্বাস্থ্য সেবা অঙ্গীকার",
    "pharmacy": "আমাদের সেবা অঙ্গীকার",
    "fitness": "আমাদের ফিটনেস লক্ষ্য",
    "automotive": "আমাদের সেবার গল্প",
    "manufacturing": "আমাদের উৎপাদন ঐতিহ্য",
    "agriculture": "আমাদের কৃষি ঐতিহ্য",
    "hotel": "আমাদের আতিথেয়তা অঙ্গীকার",
    "realestate": "আমাদের রিয়েল এস্টেট গল্প",
    "services": "আমাদের সেবা অঙ্গীকার",
    "general": "আমাদের গল্প",
}

# ── Design Tokens — Shopify 2026 ──────────────────────────────────────
CATEGORY_DESIGN: Dict[str, Dict[str, str]] = {
    "beauty": {
        "bg": "#ffffff", "primary": "#1a1a1a", "accent": "#c9a96e",
        "surface": "#fdf6f0", "hero_bg": "#fdf0f5",
        "btn_primary": "#1a1a1a", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#f0e8eb",
        "badge_bg": "#fce8f3", "badge_text": "#8b1a4a",
        "heading_font": "'Playfair Display'", "body_font": "'Inter'",
    },
    "skincare": {
        "bg": "#ffffff", "primary": "#1a1a1a", "accent": "#c9a96e",
        "surface": "#fdf6f0", "hero_bg": "#fdf0f5",
        "btn_primary": "#1a1a1a", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#f0e8eb",
        "badge_bg": "#fce8f3", "badge_text": "#8b1a4a",
        "heading_font": "'Playfair Display'", "body_font": "'Inter'",
    },
    "fashion": {
        "bg": "#ffffff", "primary": "#2c1810", "accent": "#d4a853",
        "surface": "#faf7f4", "hero_bg": "#f5ede4",
        "btn_primary": "#2c1810", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#e8ddd5",
        "badge_bg": "#fdf0e4", "badge_text": "#7a3b0a",
        "heading_font": "'Cormorant Garamond'", "body_font": "'Inter'",
    },
    "jewelry": {
        "bg": "#0d0d0d", "primary": "#c9a96e", "accent": "#ffffff",
        "surface": "#1a1a1a", "hero_bg": "#0d0d0d",
        "btn_primary": "#c9a96e", "btn_text": "#0d0d0d",
        "card_bg": "#1a1a1a", "border": "#333333",
        "badge_bg": "#c9a96e22", "badge_text": "#c9a96e",
        "heading_font": "'Cormorant Garamond'", "body_font": "'Inter'",
    },
    "baby": {
        "bg": "#ffffff", "primary": "#2d6a9f", "accent": "#f7a8c4",
        "surface": "#f0f8ff", "hero_bg": "#e8f4fd",
        "btn_primary": "#2d6a9f", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#d5eaf8",
        "badge_bg": "#e8f4fd", "badge_text": "#1a4f7a",
        "heading_font": "'Nunito'", "body_font": "'Inter'",
    },
    "home": {
        "bg": "#ffffff", "primary": "#2d4a3e", "accent": "#e8b84b",
        "surface": "#f4f7f4", "hero_bg": "#edf4ee",
        "btn_primary": "#2d4a3e", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#d5e5d8",
        "badge_bg": "#edf4ee", "badge_text": "#1a3329",
        "heading_font": "'Lora'", "body_font": "'Inter'",
    },
    "restaurant": {
        "bg": "#0f0f0f", "primary": "#d4a853", "accent": "#ffffff",
        "surface": "#1a1208", "hero_bg": "#0f0f0f",
        "btn_primary": "#d4a853", "btn_text": "#0f0f0f",
        "card_bg": "#1a1208", "border": "#2d2414",
        "badge_bg": "#d4a85322", "badge_text": "#d4a853",
        "heading_font": "'Playfair Display'", "body_font": "'Inter'",
    },
    "retail": {
        "bg": "#ffffff", "primary": "#1a1a2e", "accent": "#e94560",
        "surface": "#f8f8fc", "hero_bg": "#f0f0f8",
        "btn_primary": "#1a1a2e", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#e0e0ee",
        "badge_bg": "#fee8ec", "badge_text": "#9c0f28",
        "heading_font": "'Poppins'", "body_font": "'Inter'",
    },
    "general": {
        "bg": "#ffffff", "primary": "#1a1a2e", "accent": "#e94560",
        "surface": "#f8f8fc", "hero_bg": "#f0f0f8",
        "btn_primary": "#1a1a2e", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#e0e0ee",
        "badge_bg": "#fee8ec", "badge_text": "#9c0f28",
        "heading_font": "'Poppins'", "body_font": "'Inter'",
    },
    "healthcare": {
        "bg": "#ffffff", "primary": "#0077b6", "accent": "#00b4d8",
        "surface": "#f0f8ff", "hero_bg": "#e8f4fc",
        "btn_primary": "#0077b6", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#d0eaf8",
        "badge_bg": "#e8f4fc", "badge_text": "#005085",
        "heading_font": "'Inter'", "body_font": "'Inter'",
    },
    "pharmacy": {
        "bg": "#ffffff", "primary": "#0077b6", "accent": "#00b4d8",
        "surface": "#f0f8ff", "hero_bg": "#e8f4fc",
        "btn_primary": "#0077b6", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#d0eaf8",
        "badge_bg": "#e8f4fc", "badge_text": "#005085",
        "heading_font": "'Inter'", "body_font": "'Inter'",
    },
    "education": {
        "bg": "#ffffff", "primary": "#1b2a4a", "accent": "#f4a621",
        "surface": "#f5f7fa", "hero_bg": "#eef1f8",
        "btn_primary": "#1b2a4a", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#dde3f0",
        "badge_bg": "#fef3e2", "badge_text": "#7a5200",
        "heading_font": "'Merriweather'", "body_font": "'Inter'",
    },
    "fitness": {
        "bg": "#0a0a0a", "primary": "#ff4d00", "accent": "#ffffff",
        "surface": "#111111", "hero_bg": "#0a0a0a",
        "btn_primary": "#ff4d00", "btn_text": "#ffffff",
        "card_bg": "#1a1a1a", "border": "#2a2a2a",
        "badge_bg": "#ff4d0022", "badge_text": "#ff4d00",
        "heading_font": "'Barlow Condensed'", "body_font": "'Inter'",
    },
    "hotel": {
        "bg": "#ffffff", "primary": "#1c3145", "accent": "#c5a55a",
        "surface": "#f8f5f0", "hero_bg": "#f0ebe4",
        "btn_primary": "#1c3145", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#e0d8cc",
        "badge_bg": "#fdf5e4", "badge_text": "#6b4c00",
        "heading_font": "'Cormorant Garamond'", "body_font": "'Inter'",
    },
    "automotive": {
        "bg": "#0a0a0a", "primary": "#e63946", "accent": "#f1faee",
        "surface": "#111111", "hero_bg": "#0a0a0a",
        "btn_primary": "#e63946", "btn_text": "#ffffff",
        "card_bg": "#1a1a1a", "border": "#2a2a2a",
        "badge_bg": "#e6394622", "badge_text": "#e63946",
        "heading_font": "'Barlow'", "body_font": "'Inter'",
    },
    "realestate": {
        "bg": "#ffffff", "primary": "#2b4162", "accent": "#fa9f42",
        "surface": "#f5f7fa", "hero_bg": "#eef1f8",
        "btn_primary": "#2b4162", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#dde3f0",
        "badge_bg": "#fff3e0", "badge_text": "#7a4f00",
        "heading_font": "'Merriweather'", "body_font": "'Inter'",
    },
    "agriculture": {
        "bg": "#ffffff", "primary": "#386641", "accent": "#f2a65a",
        "surface": "#f4f8f4", "hero_bg": "#edf5ee",
        "btn_primary": "#386641", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#d5e8d6",
        "badge_bg": "#edf5ee", "badge_text": "#1a3d1f",
        "heading_font": "'Lora'", "body_font": "'Inter'",
    },
    "manufacturing": {
        "bg": "#ffffff", "primary": "#1f3a5f", "accent": "#2196f3",
        "surface": "#f5f7fa", "hero_bg": "#eef1f8",
        "btn_primary": "#1f3a5f", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#dde3f0",
        "badge_bg": "#e3f2fd", "badge_text": "#0d47a1",
        "heading_font": "'Inter'", "body_font": "'Inter'",
    },
    "services": {
        "bg": "#ffffff", "primary": "#1f3a5f", "accent": "#2196f3",
        "surface": "#f5f7fa", "hero_bg": "#eef1f8",
        "btn_primary": "#1f3a5f", "btn_text": "#ffffff",
        "card_bg": "#ffffff", "border": "#dde3f0",
        "badge_bg": "#e3f2fd", "badge_text": "#0d47a1",
        "heading_font": "'Inter'", "body_font": "'Inter'",
    },
}

GOOGLE_FONTS_URL = ("https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:wght@400;600;700&"
    "family=Inter:wght@300;400;500;600&"
    "family=Cormorant+Garamond:wght@400;600;700&"
    "family=Nunito:wght@400;600;700&"
    "family=Lora:wght@400;600;700&"
    "family=Poppins:wght@400;500;600;700&"
    "family=Merriweather:wght@400;700&"
    "family=Barlow:wght@400;500;600;700&"
    "family=Barlow+Condensed:wght@500;700&"
    "display=swap")

WHATSAPP_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">'
    '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15'
    "-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463"
    "-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133"
    ".298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149"
    "-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198"
    " 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213"
    " 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195"
    " 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124"
    "-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214"
    "-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884"
    " 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003"
    " 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16"
    " 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882"
    " 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0"
    ' 00-3.48-8.413z"/></svg>'
)

FACEBOOK_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">'
    '<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954'
    " 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669"
    " 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328"
    'l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>'
)

INSTAGRAM_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">'
    '<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058'
    " 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771"
    "-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149"
    "-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849"
    ".149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741"
    " 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0"
    " 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24"
    " 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28"
    ".073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979"
    "-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0"
    ' 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881'
    ' 1.44 1.44 0 000-2.881z"/></svg>'
)


# ── Helpers ──────────────────────────────────────────────────────────

def clean_phone_for_whatsapp(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('0'):
        digits = '880' + digits[1:]
    elif not digits.startswith('880'):
        digits = '880' + digits
    return digits


def format_phone_display(phone: str) -> str:
    raw = re.sub(r'\D', '', phone)
    if raw.startswith('880'):
        raw = raw[3:]
    raw = raw.lstrip('0')
    if len(raw) >= 10:
        return f"0{raw[:4]}-{raw[4:]}"
    return f"0{raw}"


def get_design(canonical: str) -> Dict[str, str]:
    return CATEGORY_DESIGN.get(canonical, CATEGORY_DESIGN["general"])


def fb_url(handle: str) -> str:
    if handle.startswith('http'):
        return handle
    return f"https://facebook.com/{handle}"


def ig_url(handle: str) -> str:
    if handle.startswith('http'):
        return handle
    return f"https://instagram.com/{handle}"


def product_img_url(canonical: str, idx: int) -> str:
    seed = f"{canonical}{idx}"
    return f"https://picsum.photos/seed/{seed}/400/400"


def hero_img_url(canonical: str) -> str:
    return f"https://picsum.photos/seed/{canonical}-hero/600/500"


# ── Hero Image SVG ──────────────────────────────────────────────────

def _build_hero_svg(canonical: str) -> str:
    t = get_design(canonical)
    p = t['primary']
    a = t['accent']
    s = t['surface']
    return f'''<svg viewBox="0 0 500 500" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hg" x1="0.2" y1="0" x2="0.8" y2="1">
      <stop offset="0%" stop-color="{p}" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="{a}" stop-opacity="0.10"/>
    </linearGradient>
    <linearGradient id="hg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{a}" stop-opacity="0.05"/>
    </linearGradient>
    <filter id="shadow1"><feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="{p}" flood-opacity="0.08"/></filter>
    <filter id="glow"><feGaussianBlur stdDeviation="3"/></filter>
  </defs>
  <!-- Background -->
  <rect width="500" height="500" rx="40" fill="url(#hg)"/>
  <!-- Decorative blobs -->
  <circle cx="380" cy="100" r="90" fill="url(#hg2)"/>
  <circle cx="120" cy="420" r="120" fill="url(#hg2)"/>
  <!-- Main product box -->
  <rect x="55" y="75" width="220" height="240" rx="24" fill="{s}" stroke="{p}" stroke-width="1.5" filter="url(#shadow1)"/>
  <rect x="75" y="95" width="180" height="18" rx="6" fill="{p}" opacity="0.25"/>
  <rect x="75" y="125" width="130" height="10" rx="4" fill="{p}" opacity="0.12"/>
  <rect x="75" y="148" width="110" height="10" rx="4" fill="{p}" opacity="0.12"/>
  <rect x="75" y="180" width="180" height="100" rx="12" fill="{p}" opacity="0.06"/>
  <!-- Floating circles in box -->
  <circle cx="115" cy="230" r="22" fill="{a}" opacity="0.25"/>
  <circle cx="165" cy="230" r="22" fill="{p}" opacity="0.18"/>
  <circle cx="215" cy="230" r="22" fill="{a}" opacity="0.2"/>
  <!-- Side product box -->
  <rect x="300" y="140" width="160" height="180" rx="20" fill="{s}" stroke="{a}" stroke-width="1.5" filter="url(#shadow1)"/>
  <rect x="318" y="162" width="124" height="14" rx="5" fill="{a}" opacity="0.25"/>
  <rect x="318" y="186" width="90" height="8" rx="3" fill="{a}" opacity="0.12"/>
  <rect x="318" y="206" width="100" height="8" rx="3" fill="{a}" opacity="0.12"/>
  <rect x="318" y="235" width="124" height="55" rx="8" fill="{a}" opacity="0.06"/>
  <rect x="318" y="250" width="60" height="22" rx="6" fill="{p}" opacity="0.2"/>
  <!-- Bottom bar -->
  <rect x="90" y="345" width="320" height="70" rx="18" fill="{s}" stroke="{p}" stroke-width="1" filter="url(#shadow1)"/>
  <rect x="112" y="365" width="90" height="10" rx="4" fill="{p}" opacity="0.18"/>
  <rect x="218" y="365" width="140" height="10" rx="4" fill="{p}" opacity="0.1"/>
  <rect x="112" y="383" width="60" height="6" rx="3" fill="{a}" opacity="0.12"/>
  <!-- Stars / sparkles -->
  <circle cx="430" cy="80" r="6" fill="{a}" opacity="0.35"/>
  <circle cx="450" cy="100" r="3" fill="{a}" opacity="0.2"/>
  <circle cx="80" cy="60" r="5" fill="{p}" opacity="0.25"/>
  <circle cx="460" cy="430" r="7" fill="{p}" opacity="0.15"/>
  <!-- Bottom decorative line -->
  <path d="M60 450 L250 450 L210 480 L100 480 Z" fill="{p}" opacity="0.05"/>
  <path d="M260 450 L440 450 L400 480 L300 480 Z" fill="{a}" opacity="0.04"/>
</svg>'''


# ── Brand Logo SVG ──────────────────────────────────────────────────

def _build_logo_svg(canonical: str) -> str:
    t = get_design(canonical)
    p = t['primary']
    a = t['accent']
    return '''<svg class="brand-logo-svg" width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="32" height="32" rx="10" fill="''' + p + '''"/>
  <path d="M18 8 L24 16 L18 28 L12 16 Z" fill="white" opacity="0.9"/>
  <path d="M18 12 L21 16 L18 24 L15 16 Z" fill="''' + a + '''" opacity="0.8"/>
  <rect x="8" y="6" width="3" height="3" rx="1.5" fill="white" opacity="0.3"/>
  <rect x="25" y="23" width="3" height="3" rx="1.5" fill="white" opacity="0.2"/>
</svg>'''


# ── Shared Header / Footer ──────────────────────────────────────────

NAV_ITEMS = [
    ("/", "home", "হোম", "Home"),
    ("products.html", "products", "প্রোডাক্ট", "Products"),
    ("about.html", "about", "আমাদের সম্পর্কে", "About Us"),
    ("contact.html", "contact", "যোগাযোগ", "Contact"),
    ("order.html", "order", "অর্ডার করুন", "Order Now"),
]


def _build_header(name: str, phone: str, canonical: str, active: str) -> str:
    wa = clean_phone_for_whatsapp(phone)
    logo_svg = _build_logo_svg(canonical)
    nav_links = '\n'.join(
        f'      <a href="{href}"{" class=\"active\"" if page == active else ""}>'
        f'<span class="lang-bn">{bn}</span><span class="lang-en">{en}</span></a>'
        for href, page, bn, en in NAV_ITEMS
    )
    return f'''<header class="header" id="header">
  <div class="container header-inner">
    <a href="/" class="logo">
      {logo_svg}
      <span class="logo-name">{name}</span>
    </a>
    <nav class="nav" id="mainNav">
{nav_links}
    </nav>
    <div class="header-actions">
      <button class="lang-toggle" id="langToggle" aria-label="Language">EN | বাংলা</button>
      <a href="order.html" class="cart-icon" aria-label="Cart">🛒</a>
      <a href="login.html" class="account-icon" aria-label="Account">👤</a>
      <button class="menu-toggle" id="menuToggle" aria-label="Menu">☰</button>
    </div>
  </div>
</header>'''


def _build_footer(name: str, phone: str, canonical: str, address: str,
                  facebook_url: str = '', instagram: str = '',
                  store_type: str = 'store', bengali_name: str = '') -> str:
    wa = clean_phone_for_whatsapp(phone)
    phone_disp = format_phone_display(phone)
    fb = facebook_url if facebook_url else '#'
    fb_link = f'<a href="{fb}" target="_blank" aria-label="Facebook">{FACEBOOK_SVG}</a>' if facebook_url else ''
    ig_link = f'<a href="{ig_url(instagram)}" target="_blank" aria-label="Instagram">{INSTAGRAM_SVG}</a>' if instagram else ''
    wa_link = f'<a href="https://wa.me/{wa}" target="_blank" aria-label="WhatsApp">{WHATSAPP_SVG}</a>'

    nav_footer = '\n'.join(
        f'        <a href="{href}"><span class="lang-bn">{bn}</span><span class="lang-en">{en}</span></a>'
        for href, _, bn, en in NAV_ITEMS
    )

    return f'''<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="footer-logo">
          {_build_logo_svg(canonical)}
          <span>{name}</span>
        </div>
        <p>
          <span class="lang-bn">{bengali_name} — আপনার বিশ্বস্ত অনলাইন শপিং গন্তব্য</span>
          <span class="lang-en">{name} — Your trusted {store_type} destination</span>
        </p>
        <div class="footer-social">
          {fb_link}{ig_link}{wa_link}
        </div>
      </div>
      <div class="footer-col">
        <h4><span class="lang-bn">দ্রুত লিংক</span><span class="lang-en">Quick Links</span></h4>
{nav_footer}
      </div>
      <div class="footer-col">
        <h4><span class="lang-bn">যোগাযোগ</span><span class="lang-en">Contact</span></h4>
        <p>📞 <a href="tel:{phone_disp}" style="color:rgba(255,255,255,0.6)">{phone_disp}</a></p>
        <p>📍 {address}</p>
      </div>
      <div class="footer-col">
        <h4><span class="lang-bn">ব্যবসায়িক সময়</span><span class="lang-en">Business Hours</span></h4>
        <p><span class="lang-bn">শনি-বৃহস্পতি: ৯AM-৯PM</span><span class="lang-en">Sat-Thu: 9AM-9PM</span></p>
        <p><span class="lang-bn">শুক্রবার: বন্ধ</span><span class="lang-en">Friday: Closed</span></p>
        <div style="margin-top:12px">
          <span class="trust-icon">🚚</span> <span class="lang-bn">ফ্রি ডেলিভারি</span><span class="lang-en">Free Delivery</span><br>
          <span class="trust-icon">💳</span> <span class="lang-bn">ক্যাশ অন ডেলিভারি</span><span class="lang-en">Cash on Delivery</span>
        </div>
      </div>
    </div>
    <div class="footer-newsletter">
      <form class="footer-newsletter-form" id="footerNewsletterForm">
        <label>
          <span class="lang-bn">সাবস্ক্রাইব করুন</span>
          <span class="lang-en">Subscribe</span>
        </label>
        <div class="footer-newsletter-input-row">
          <input type="email" id="footerNewsletterEmail" required
            placeholder="your@email.com"
            aria-label="Email address">
          <button type="submit">→</button>
        </div>
      </form>
    </div>
    <div class="footer-bottom">
      <span class="lang-bn">© 2026 {name} — সর্বস্বত্ব সংরক্ষিত</span>
      <span class="lang-en">© 2026 {name} — All rights reserved</span>
    </div>
  </div>
</footer>'''


def _build_wa_float(phone: str) -> str:
    wa = clean_phone_for_whatsapp(phone)
    return f'''<a href="https://wa.me/{wa}" target="_blank" class="wa-float" aria-label="WhatsApp">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>'''


# ── CSS Builder (FIX 2 + FIX 6) ──────────────────────────────────────

def _build_css(canonical: str, primary_color: Optional[str] = None, accent_color: Optional[str] = None) -> str:
    t = dict(get_design(canonical))
    if primary_color:
        t['primary'] = primary_color
        t['btn_primary'] = primary_color
    if accent_color:
        t['accent'] = accent_color
    return f'''@import url('{GOOGLE_FONTS_URL}');

:root {{
  --bg: {t['bg']};
  --primary: {t['primary']};
  --accent: {t['accent']};
  --surface: {t['surface']};
  --hero-bg: {t['hero_bg']};
  --btn-primary: {t['btn_primary']};
  --btn-text: {t['btn_text']};
  --card-bg: {t['card_bg']};
  --border: {t['border']};
  --badge-bg: {t['badge_bg']};
  --badge-text: {t['badge_text']};
  --font-heading: {t['heading_font']};
  --font-body: {t['body_font']};
  --text: #1C1917;
  --text-muted: #78716C;
  --radius: 12px;
  --radius-sm: 8px;
  --radius-full: 9999px;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-hover: 0 10px 25px rgba(0,0,0,0.08);
  --transition: 0.25s ease;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; scroll-padding-top:80px; }}
body {{
  font-family:var(--font-body);
  background:var(--bg);
  color:var(--text);
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
}}
::selection {{ background:color-mix(in srgb, var(--primary) 20%, transparent); }}
img {{ max-width:100%; height:auto; display:block; }}
a {{ color:var(--primary); text-decoration:none; transition:color var(--transition); }}
a:hover {{ color:var(--accent); }}
.container {{ max-width:1120px; margin:0 auto; padding:0 24px; }}

h1, h2, h3, .hero-title, .product-name {{ font-family:var(--font-heading); }}
body, p, input, button, select {{ font-family:var(--font-body); }}

.lang-en {{ display:inline; }}
.lang-bn {{ display:none; }}
html[lang="bn"] .lang-bn {{ display:inline; }}
html[lang="bn"] .lang-en {{ display:none; }}

/* ── Announcement Bar ── */
.announcement-bar {{
  background:var(--primary); color:#fff; text-align:center;
  padding:10px 16px; font-size:13px; font-weight:500;
  position:relative; z-index:101; overflow:hidden; white-space:nowrap;
}}
.announcement-bar .marquee-wrap {{
  display:inline-block;
  animation:marquee 20s linear infinite;
}}
.announcement-bar .marquee-wrap:hover {{
  animation-play-state:paused;
}}
@keyframes marquee {{
  0% {{ transform:translateX(100vw); }}
  100% {{ transform:translateX(-100%); }}
}}
.announcement-close {{
  position:absolute; right:16px; top:50%; transform:translateY(-50%);
  background:none; border:none; color:#fff; font-size:18px; cursor:pointer;
  opacity:0.7; line-height:1; z-index:2;
}}
.announcement-close:hover {{ opacity:1; }}

/* ── Header ── */
.header {{
  position:sticky; top:0; left:0; right:0; z-index:100;
  height:64px;
  background:rgba(255,255,255,0.95);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  border-bottom:1px solid var(--border);
  transition:box-shadow var(--transition);
}}
.header.scrolled {{ box-shadow:0 2px 20px rgba(0,0,0,0.06); }}
.header-inner {{
  display:flex; align-items:center; justify-content:space-between; height:100%;
}}
.logo {{
  display:flex; align-items:center; gap:10px; text-decoration:none;
}}
.brand-logo-svg {{
  flex-shrink:0;
}}
.logo-name {{
  font-family:var(--font-heading);
  font-size:17px; font-weight:700; color:var(--text);
}}
.nav {{ display:flex; align-items:center; gap:4px; }}
.nav a {{
  padding:8px 14px; border-radius:var(--radius-sm);
  font-size:14px; font-weight:500; color:var(--text-muted);
  transition:all var(--transition); text-decoration:none;
}}
.nav a:hover, .nav a.active {{ color:var(--primary); background:color-mix(in srgb, var(--primary) 8%, transparent); }}
.header-actions {{ display:flex; align-items:center; gap:6px; }}
.lang-toggle {{
  padding:6px 12px; border:1px solid var(--border); border-radius:var(--radius-sm);
  background:transparent; font-size:12px; font-weight:500; cursor:pointer;
  color:var(--text-muted); transition:all var(--transition);
}}
.lang-toggle:hover {{ border-color:var(--primary); color:var(--primary); }}
.wa-header-btn {{
  display:flex; align-items:center; justify-content:center;
  width:36px; height:36px; border-radius:50%;
  color:#25D366; transition:all var(--transition);
}}
.wa-header-btn:hover {{ background:color-mix(in srgb, var(--primary) 8%, transparent); }}
.cart-icon {{
  display:flex; align-items:center; justify-content:center;
  width:36px; height:36px; border-radius:50%;
  color:var(--text); transition:all var(--transition);
  font-size:18px;
}}
.cart-icon:hover {{ background:color-mix(in srgb, var(--primary) 8%, transparent); }}
.menu-toggle {{
  display:none; background:none; border:none;
  font-size:24px; cursor:pointer; color:var(--text);
  width:40px; height:40px; align-items:center; justify-content:center;
}}

/* ── Hero ── */
.hero {{
  position:relative; min-height:80vh;
  display:grid; grid-template-columns:1fr 1fr; gap:60px; align-items:center;
  background:var(--hero-bg); overflow:hidden; padding:80px 60px;
}}
.hero-content {{ position:relative; z-index:2; max-width:520px; }}
.hero-left {{ text-align:left; }}
.hero-center {{ text-align:left; }}
.hero-image {{
  position:relative; z-index:2; display:flex; align-items:center; justify-content:center;
}}
.hero-image img {{
  width:100%; max-width:550px; height:auto; border-radius:28px;
  object-fit:cover; aspect-ratio:5/4;
  box-shadow:0 25px 80px rgba(0,0,0,0.15);
  animation:hero-float 6s ease-in-out infinite;
}}
@keyframes hero-float {{
  0%,100% {{ transform:translateY(0); }}
  50% {{ transform:translateY(-12px); }}
}}
.hero-tagline {{
  font-size:14px; color:var(--text-muted); margin-bottom:8px; letter-spacing:0.03em;
}}
.hero-tagline .lang-bn {{
  font-family:var(--font-heading);
}}
.hero h1 {{
  font-family:var(--font-heading);
  font-size:clamp(40px, 5.5vw, 64px); font-weight:900;
  line-height:1.06; letter-spacing:-0.03em;
  margin-bottom:20px;
}}
.hero-sub {{
  font-size:18px; color:var(--text-muted);
  max-width:540px; line-height:1.5; margin-bottom:16px;
}}
.hero-address {{ font-size:14px; color:var(--text-muted); margin-bottom:32px; }}
.hero-actions {{ display:flex; gap:12px; flex-wrap:wrap; }}

/* ── Buttons ── */
.btn {{
  display:inline-flex; align-items:center; gap:8px; justify-content:center;
  padding:14px 28px; border-radius:var(--radius-sm);
  font-size:15px; font-weight:600; text-decoration:none;
  border:none; cursor:pointer;
  transition:all var(--transition);
}}
.btn-primary {{
  background:var(--btn-primary); color:var(--btn-text);
}}
.btn-primary:hover {{ transform:translateY(-2px); opacity:0.92; }}
.btn-ghost {{
  background:transparent; color:var(--primary);
  border:1.5px solid color-mix(in srgb, var(--primary) 40%, transparent);
}}
.btn-ghost:hover {{ border-color:var(--primary); background:color-mix(in srgb, var(--primary) 8%, transparent); }}
.btn-wa {{
  background:#25D366; color:#fff;
}}
.btn-wa:hover {{ background:#1da851; }}
.btn-sm {{ padding:10px 18px; font-size:13px; }}
.btn-lg {{ padding:16px 36px; font-size:16px; }}

/* ── Trust Bar ── */
.trust-bar {{ padding:20px 0; background:var(--surface); }}
.trust-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }}
.trust-item {{
  display:flex; align-items:center; gap:10px;
  font-size:13px; font-weight:500; justify-content:center;
  color:var(--text-muted);
}}
.trust-icon {{ font-size:20px; }}

/* ── Section ── */
.section {{ padding:60px 0; }}
.section-shaded {{ background:var(--surface); }}
.section-head {{ text-align:center; margin-bottom:40px; }}
.eyebrow {{
  display:inline-block; font-size:12px; font-weight:600;
  letter-spacing:0.06em; text-transform:uppercase;
  color:var(--primary); margin-bottom:8px;
}}
.section-head h2 {{
  font-family:var(--font-heading);
  font-size:clamp(22px, 3vw, 32px); font-weight:800;
  letter-spacing:-0.01em; margin-bottom:8px;
}}

/* ── Products Grid (Home) ── */
.products-grid {{
  display:grid; grid-template-columns:repeat(4,1fr); gap:20px;
}}
.product-card {{
  background:var(--card-bg); border-radius:var(--radius);
  border:1px solid var(--border); overflow:hidden;
  transition:all var(--transition);
}}
.product-card:hover {{ transform:translateY(-4px); box-shadow:var(--shadow-hover); }}
.product-img-wrap {{
  position:relative; aspect-ratio:1/1; overflow:hidden;
}}
.product-img-wrap img {{
  width:100%; height:100%; object-fit:cover;
  transition:transform 0.4s;
}}
.product-card:hover .product-img-wrap img {{ transform:scale(1.06); }}
.product-badge {{
  position:absolute; top:12px; left:12px;
  padding:4px 12px; border-radius:var(--radius-full);
  background:var(--badge-bg); color:var(--badge-text);
  font-size:11px; font-weight:600;
}}
.product-body {{ padding:16px; }}
.product-name {{
  font-family:var(--font-heading);
  font-size:15px; font-weight:600; margin-bottom:4px;
}}
.product-desc {{ font-size:13px; color:var(--text-muted); margin-bottom:8px; line-height:1.4; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }}
.product-price {{ font-size:18px; font-weight:700; color:var(--primary); margin-bottom:12px; }}
.product-actions {{ display:flex; gap:8px; }}
.product-actions .btn {{ flex:1; font-size:13px; padding:10px 12px; }}
.product-wa-btn {{
  width:40px; height:40px; border-radius:var(--radius-sm);
  background:#25D366; color:#fff;
  display:flex; align-items:center; justify-content:center;
  flex-shrink:0; transition:all var(--transition);
}}
.product-wa-btn:hover {{ transform:scale(1.05); }}

/* ── Category Pills ── */
.category-pills {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-bottom:40px; }}
.category-pill {{
  padding:8px 20px; border-radius:var(--radius-full);
  border:1px solid var(--border); background:var(--card-bg);
  font-size:13px; font-weight:500; cursor:pointer;
  color:var(--text-muted); transition:all var(--transition);
}}
.category-pill:hover, .category-pill.active {{ background:var(--primary); color:var(--btn-text); border-color:var(--primary); }}

/* ── About Teaser ── */
.about-teaser {{ display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center; }}
.about-teaser-img {{
  aspect-ratio:4/3; border-radius:var(--radius);
  overflow:hidden; background:var(--surface);
}}
.about-teaser-img img {{ width:100%; height:100%; object-fit:cover; }}
.about-teaser-text h3 {{
  font-family:var(--font-heading);
  font-size:26px; font-weight:700; margin-bottom:12px;
}}
.about-teaser-text p {{ font-size:15px; color:var(--text-muted); line-height:1.7; margin-bottom:16px; }}

/* ── Why Choose ── */
.why-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }}
.why-card {{
  background:var(--card-bg); border-radius:var(--radius);
  padding:28px 20px; text-align:center;
  border:1px solid var(--border);
  transition:all var(--transition);
}}
.why-card:hover {{ transform:translateY(-2px); box-shadow:var(--shadow-hover); }}
.why-icon {{ font-size:32px; display:block; margin-bottom:12px; }}
.why-card h4 {{ font-size:15px; font-weight:700; margin-bottom:6px; }}
.why-card p {{ font-size:13px; color:var(--text-muted); line-height:1.5; }}

/* ── Reviews ── */
.reviews-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }}
.review-card {{
  background:var(--card-bg); border-radius:var(--radius);
  padding:24px 20px; border:1px solid var(--border);
  border-left:4px solid var(--primary);
  transition:all var(--transition);
}}
.review-card:hover {{ box-shadow:var(--shadow-hover); }}
.review-stars {{ color:#f59e0b; font-size:14px; margin-bottom:10px; letter-spacing:2px; }}
.review-text {{ font-size:14px; color:var(--text-muted); font-style:italic; line-height:1.6; margin-bottom:12px; }}
.review-author {{ font-size:13px; font-weight:600; }}
.review-location {{ font-size:12px; color:var(--text-muted); }}

/* ── Social CTA ── */
.social-cta {{
  padding:48px 0; text-align:center;
  background:var(--primary); color:#fff;
}}
.social-cta h2 {{
  font-family:var(--font-heading);
  font-size:24px; font-weight:700; margin-bottom:8px; color:#fff;
}}
.social-cta p {{ font-size:15px; opacity:0.9; margin-bottom:20px; }}
.social-cta .btn {{ background:#fff; color:var(--primary); }}
.social-cta .btn:hover {{ background:color-mix(in srgb, #fff 90%, transparent); }}

/* ── Footer ── */
.footer {{
  background:#1a1a1a; color:rgba(255,255,255,0.7); padding:48px 0 0;
}}
.footer-grid {{ display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:40px; }}
.footer-brand h3 {{
  font-family:var(--font-heading);
  font-size:18px; font-weight:700; color:#fff; margin-bottom:8px;
}}
.footer-brand p {{ font-size:14px; line-height:1.6; margin-bottom:12px; }}
.footer-social {{ display:flex; gap:10px; }}
.footer-social a {{
  display:flex; align-items:center; justify-content:center;
  width:36px; height:36px; border-radius:50%;
  background:rgba(255,255,255,0.1); color:rgba(255,255,255,0.7);
  transition:all var(--transition);
}}
.footer-logo {{
  display:flex; align-items:center; gap:10px; margin-bottom:8px;
}}
.footer-logo span {{
  font-family:var(--font-heading); font-size:20px; font-weight:700; color:#fff;
}}
.footer-social a:hover {{ background:var(--primary); color:#fff; }}
.footer-col h4 {{ font-size:13px; font-weight:700; color:#fff; margin-bottom:14px; text-transform:uppercase; letter-spacing:0.05em; }}
.footer-col a {{ display:block; font-size:14px; color:rgba(255,255,255,0.6); margin-bottom:8px; }}
.footer-col a:hover {{ color:#fff; }}
.footer-col p {{ font-size:14px; color:rgba(255,255,255,0.6); margin-bottom:6px; }}
.footer-bottom {{
  border-top:1px solid rgba(255,255,255,0.08);
  margin-top:32px; padding:20px 0;
  text-align:center; font-size:13px; color:rgba(255,255,255,0.4);
}}
.footer-newsletter {{
  border-top:1px solid rgba(255,255,255,0.08);
  padding:24px 0; margin-top:24px;
}}
.footer-newsletter label {{
  font-size:14px; font-weight:600; color:#fff;
  display:block; margin-bottom:10px;
}}
.footer-newsletter-input-row {{
  display:flex; gap:8px; max-width:400px;
}}
.footer-newsletter-input-row input {{
  flex:1; padding:12px 16px; border-radius:var(--radius-sm);
  border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.06);
  color:#fff; font-size:14px; outline:none;
}}
.footer-newsletter-input-row input::placeholder {{ color:rgba(255,255,255,0.4); }}
.footer-newsletter-input-row input:focus {{ border-color:var(--primary); }}
.footer-newsletter-input-row button {{
  width:44px; height:44px; border-radius:var(--radius-sm);
  background:var(--primary); color:#fff; border:none;
  font-size:18px; cursor:pointer; transition:all var(--transition);
}}
.footer-newsletter-input-row button:hover {{ opacity:0.9; transform:translateX(2px); }}

/* ── WhatsApp Float ── */
.toast {{
  position:fixed; bottom:90px; left:50%; transform:translateX(-50%) translateY(20px);
  background:#1a1a1a; color:#fff; padding:14px 28px; border-radius:var(--radius);
  font-size:15px; font-weight:500; z-index:10000; opacity:0; pointer-events:none;
  transition:all 0.4s ease; box-shadow:0 8px 32px rgba(0,0,0,0.15);
}}
.toast.show {{ opacity:1; transform:translateX(-50%) translateY(0); }}

.wa-float {{
  position:fixed; bottom:24px; right:24px; z-index:999;
  width:56px; height:56px; border-radius:50%;
  background:#25D366; color:#fff;
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 4px 20px rgba(37,211,102,0.4);
  transition:all var(--transition);
  animation:wa-pulse 2s infinite;
}}
@keyframes wa-pulse {{
  0% {{ box-shadow:0 4px 20px rgba(37,211,102,0.4); }}
  50% {{ box-shadow:0 4px 30px rgba(37,211,102,0.6); }}
  100% {{ box-shadow:0 4px 20px rgba(37,211,102,0.4); }}
}}
.wa-float:hover {{ transform:scale(1.1); }}
.wa-float svg {{ width:28px; height:28px; fill:#fff; }}

/* ── Page Hero ── */
.page-hero {{
  padding:48px 0 32px; background:var(--hero-bg); text-align:center;
}}
.page-hero-sm {{ padding:32px 0 24px; }}
.page-hero h1 {{
  font-family:var(--font-heading);
  font-size:clamp(24px, 3vw, 34px); font-weight:800; margin-bottom:8px;
}}
.page-hero p {{ font-size:15px; color:var(--text-muted); }}

/* ── Products Page ── */
.filter-bar {{
  display:flex; gap:8px; flex-wrap:wrap; justify-content:center;
  margin-bottom:32px; align-items:center;
}}
.filter-btn {{
  padding:8px 20px; border-radius:var(--radius-full);
  border:1px solid var(--border); background:var(--card-bg);
  font-size:13px; font-weight:500; cursor:pointer;
  color:var(--text-muted); transition:all var(--transition);
}}
.filter-btn:hover, .filter-btn.active {{ background:var(--primary); color:var(--btn-text); border-color:var(--primary); }}

/* ── Order Page ── */
.order-grid {{ display:grid; grid-template-columns:3fr 2fr; gap:32px; align-items:start; }}
.order-form-card {{
  background:var(--card-bg); border-radius:var(--radius);
  border:1px solid var(--border); padding:24px;
}}
.order-form-card h3 {{
  font-family:var(--font-heading);
  font-size:18px; font-weight:700; margin-bottom:20px;
  padding-bottom:12px; border-bottom:1px solid var(--border);
}}
.form-group {{ margin-bottom:16px; }}
.form-group label {{ display:block; font-size:14px; font-weight:500; margin-bottom:6px; }}
.form-group input,
.form-group select,
.form-group textarea {{
  width:100%; padding:12px 16px; border:1px solid var(--border);
  border-radius:var(--radius-sm); font-size:14px;
  background:var(--bg); outline:none; transition:all var(--transition);
}}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {{
  border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}}
.form-group textarea {{ min-height:80px; resize:vertical; }}
.form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.submit-btn {{
  width:100%; padding:14px; font-size:16px; border-radius:var(--radius);
  background:var(--btn-primary); color:var(--btn-text);
  border:none; cursor:pointer; font-weight:600;
  transition:all var(--transition); height:48px;
}}
.submit-btn:hover {{ opacity:0.92; transform:translateY(-1px); }}

.order-summary-card {{
  background:var(--card-bg); border-radius:var(--radius);
  border:1px solid var(--border); padding:24px;
  position:sticky; top:88px;
}}
.order-summary-card h3 {{
  font-family:var(--font-heading);
  font-size:18px; font-weight:700; margin-bottom:16px;
  padding-bottom:12px; border-bottom:1px solid var(--border);
}}
.order-summary-row {{
  display:flex; justify-content:space-between; padding:8px 0;
  font-size:14px; border-bottom:1px solid var(--border);
}}
.order-summary-row:last-child {{ border-bottom:none; }}
.summary-value {{ font-weight:500; }}
.order-summary-total {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; font-size:16px; font-weight:700; color:var(--primary);
  border-top:2px solid var(--primary); margin-top:8px;
}}
.summary-trust {{
  margin-top:16px; padding-top:12px; border-top:1px solid var(--border);
}}
.summary-trust-item {{
  display:flex; align-items:center; gap:8px;
  font-size:13px; color:var(--text-muted); margin-bottom:6px;
}}
.summary-contact {{
  margin-top:12px; padding-top:12px; border-top:1px solid var(--border);
  font-size:14px; text-align:center;
}}
.order-form-section {{
  margin-bottom:24px;
}}
.order-form-section-title {{
  font-family:var(--font-heading);
  font-size:15px; font-weight:600; margin-bottom:14px;
  color:var(--text); display:flex; align-items:center; gap:8px;
}}
.order-form-section-title::before {{
  content:''; width:3px; height:16px; background:var(--primary); border-radius:2px;
}}

/* ── Cart Items ── */
.cart-item {{
  display:flex; align-items:center; gap:12px;
  padding:14px 0; border-bottom:1px solid var(--border);
}}
.cart-item:first-child {{ padding-top:0; }}
.cart-item-img {{
  width:48px; height:48px; border-radius:var(--radius-sm);
  background:var(--hero-bg); display:flex; align-items:center;
  justify-content:center; font-weight:700; color:var(--primary);
  font-size:14px; flex-shrink:0;
}}
.cart-item-body {{ flex:1; min-width:0; }}
.cart-item-name {{ font-size:14px; font-weight:600; }}
.cart-item-price {{ font-size:13px; color:var(--text-muted); margin-top:2px; }}
.cart-item-qty {{ display:flex; align-items:center; gap:6px; }}
.cart-qty-btn {{
  width:30px; height:30px; border-radius:50%;
  border:1px solid var(--border); background:var(--bg);
  cursor:pointer; font-size:16px; display:flex;
  align-items:center; justify-content:center;
  transition:all var(--transition); line-height:1;
}}
.cart-qty-btn:hover {{ border-color:var(--primary); color:var(--primary); }}
.cart-qty-val {{ font-size:15px; font-weight:600; min-width:20px; text-align:center; }}
.cart-item-total {{ font-size:15px; font-weight:700; min-width:60px; text-align:right; }}
.cart-note {{ margin-top:20px; }}
.cart-note label {{ display:block; font-size:14px; font-weight:500; margin-bottom:6px; }}
.cart-note textarea {{ width:100%; padding:12px 16px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:14px; background:var(--bg); outline:none; resize:vertical; min-height:60px; }}
.cart-note textarea:focus {{ border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent); }}

/* ── Order Confirmation ── */
.order-confirm-card {{
  max-width:580px; margin:0 auto; text-align:center;
  background:var(--surface); border-radius:var(--radius-xl);
  padding:48px 40px; border:1px solid var(--border);
}}
.confirm-icon {{
  font-size:56px; margin-bottom:16px;
}}
.order-confirm-card h2 {{
  font-family:var(--font-heading); font-size:26px; margin-bottom:8px;
}}
.confirm-subtitle {{
  color:var(--text-muted); font-size:15px; margin-bottom:28px; line-height:1.5;
}}
.confirm-details {{
  text-align:left; background:var(--bg); padding:20px 24px;
  border-radius:var(--radius); margin-bottom:20px;
}}
.confirm-row {{
  display:flex; justify-content:space-between; padding:6px 0;
  font-size:14px; border-bottom:1px solid var(--border);
}}
.confirm-row:last-child {{ border-bottom:none; }}
.confirm-items {{
  text-align:left; background:var(--bg); padding:16px 24px;
  border-radius:var(--radius); margin-bottom:16px;
}}
.confirm-item {{
  display:flex; justify-content:space-between; padding:4px 0;
  font-size:14px; color:var(--text-muted);
}}
.confirm-message {{
  color:var(--text-muted); font-size:14px; line-height:1.6;
}}
.checkout-steps {{
  display:flex; justify-content:center; gap:8px; margin-bottom:32px;
}}
.checkout-steps .step {{
  display:flex; align-items:center; gap:8px;
  padding:10px 20px; border-radius:var(--radius-full);
  background:var(--surface); font-size:14px; font-weight:500;
  color:var(--text-muted); border:1px solid var(--border);
}}
.checkout-steps .step.active {{
  background:var(--primary); color:#fff; border-color:var(--primary);
}}
.step-num {{
  display:inline-flex; align-items:center; justify-content:center;
  width:24px; height:24px; border-radius:50%;
  background:rgba(0,0,0,0.1); font-size:12px; font-weight:700;
}}
.checkout-steps .step.active .step-num {{
  background:rgba(255,255,255,0.25);
}}

/* ── Payment Options ── */
.payment-options {{ display:flex; flex-direction:column; gap:10px; }}
.payment-option {{
  display:flex; align-items:center; gap:14px; padding:14px 16px;
  border:1.5px solid var(--border); border-radius:var(--radius-sm);
  cursor:pointer; transition:all var(--transition); position:relative;
}}
.payment-option:hover {{ border-color:var(--primary); background:color-mix(in srgb, var(--primary) 4%, transparent); }}
.payment-option input[type="radio"] {{ position:absolute; opacity:0; }}
.payment-option input[type="radio"]:checked + .payment-radio {{
  border-color:var(--primary); background:var(--primary);
  box-shadow:inset 0 0 0 3px var(--bg);
}}
.payment-option:has(input:checked) {{ border-color:var(--primary); background:color-mix(in srgb, var(--primary) 6%, transparent); }}
.payment-radio {{
  width:20px; height:20px; border-radius:50%; border:2px solid var(--border);
  flex-shrink:0; transition:all var(--transition);
}}
.payment-info {{ flex:1; }}
.payment-name {{ font-size:15px; font-weight:600; display:block; }}
.payment-desc {{ font-size:12px; color:var(--text-muted); margin-top:2px; }}

/* ── About Page ── */
.about-grid {{
  display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center;
}}
.about-story h2 {{
  font-family:var(--font-heading); font-size:28px; margin-bottom:16px;
}}
.about-story p {{
  color:var(--text-muted); line-height:1.7; margin-bottom:16px; font-size:15px;
}}
.about-stats {{
  display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:40px;
}}
.about-stat {{
  text-align:center; padding:24px; background:var(--surface); border-radius:var(--radius);
}}
.about-stat .stat-icon {{ font-size:32px; margin-bottom:8px; display:block; }}
.about-stat .stat-val {{ font-size:28px; font-weight:700; color:var(--primary); }}
.about-stat .stat-label {{ font-size:13px; color:var(--text-muted); margin-top:4px; }}
.about-mission {{
  background:var(--surface); padding:48px; border-radius:var(--radius-xl);
  margin-top:40px; text-align:center;
}}
.about-mission h2 {{ font-family:var(--font-heading); font-size:24px; margin-bottom:12px; }}
.about-mission p {{ max-width:600px; margin:0 auto; color:var(--text-muted); line-height:1.7; }}
.about-values {{
  display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:40px;
}}
.value-card {{
  padding:32px 24px; background:var(--surface); border-radius:var(--radius);
  text-align:center; border:1px solid var(--border);
}}
.value-card .value-icon {{ font-size:36px; margin-bottom:12px; display:block; }}
.value-card h3 {{ font-size:16px; margin-bottom:8px; }}
.value-card p {{ font-size:13px; color:var(--text-muted); line-height:1.6; }}

/* ── Contact Page ── */
.contact-grid {{
  display:grid; grid-template-columns:1fr 1fr; gap:48px;
}}
.contact-info-card {{
  background:var(--surface); border-radius:var(--radius); padding:32px;
  border:1px solid var(--border);
}}
.contact-info-card h2 {{
  font-family:var(--font-heading); font-size:20px; margin-bottom:24px;
}}
.contact-item {{
  display:flex; align-items:flex-start; gap:14px; margin-bottom:20px;
}}
.contact-item .ci-icon {{ font-size:20px; margin-top:2px; }}
.contact-item .ci-label {{ font-size:13px; color:var(--text-muted); }}
.contact-item .ci-value {{ font-weight:500; }}
.contact-form-card {{
  background:var(--surface); border-radius:var(--radius); padding:32px;
  border:1px solid var(--border);
}}
.contact-form-card h2 {{
  font-family:var(--font-heading); font-size:20px; margin-bottom:24px;
}}
.contact-form-card .form-group {{ margin-bottom:16px; }}
.contact-form-card label {{ display:block; font-size:14px; font-weight:500; margin-bottom:6px; }}
.contact-form-card input,
.contact-form-card textarea,
.contact-form-card select {{
  width:100%; padding:12px 14px; border:1.5px solid var(--border);
  border-radius:var(--radius-sm); font-size:14px; background:var(--bg);
  color:var(--text); transition:border-color var(--transition);
}}
.contact-form-card input:focus,
.contact-form-card textarea:focus {{
  outline:none; border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}}
.contact-map-placeholder {{
  width:100%; height:240px; background:var(--hero-bg); border-radius:var(--radius);
  display:flex; align-items:center; justify-content:center; margin-top:32px;
  color:var(--text-muted); font-size:14px;
}}

/* ── Newsletter Section ── */
.newsletter-section {{
  padding:60px 0;
}}
.newsletter-card {{
  background:var(--surface); border-radius:var(--radius-xl);
  padding:48px 40px; display:flex; align-items:center;
  justify-content:space-between; gap:32px;
  border:1px solid var(--border);
}}
.newsletter-text h2 {{
  font-family:var(--font-heading); font-size:22px; margin-bottom:8px;
}}
.newsletter-text p {{
  color:var(--text-muted); font-size:14px; max-width:400px;
}}
.newsletter-form {{
  display:flex; gap:8px; flex-shrink:0;
}}
.newsletter-form input {{
  width:280px; padding:14px 18px; border:1.5px solid var(--border);
  border-radius:var(--radius-sm); font-size:15px; outline:none;
  background:var(--bg); color:var(--text);
  transition:border-color var(--transition);
}}
.newsletter-form input:focus {{
  border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}}
.newsletter-form button {{
  padding:14px 28px; background:var(--btn-primary); color:var(--btn-text);
  border:none; border-radius:var(--radius-sm); font-size:15px; font-weight:600;
  cursor:pointer; transition:all var(--transition); white-space:nowrap;
}}
.newsletter-form button:hover {{ transform:translateY(-2px); opacity:0.92; }}

/* ── Auth Pages (Login / Register) ── */
.auth-wrapper {{
  max-width:440px; margin:0 auto; padding:40px 24px;
}}
.auth-card {{
  background:var(--surface); border-radius:var(--radius-xl); padding:40px;
  border:1px solid var(--border); box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
.auth-card h1 {{
  font-family:var(--font-heading); font-size:24px; text-align:center; margin-bottom:4px;
}}
.auth-card .auth-subtitle {{
  text-align:center; color:var(--text-muted); font-size:14px; margin-bottom:28px;
}}
.auth-card .form-group {{ margin-bottom:18px; }}
.auth-card label {{ display:block; font-size:14px; font-weight:500; margin-bottom:6px; }}
.auth-card input[type="text"],
.auth-card input[type="email"],
.auth-card input[type="tel"],
.auth-card input[type="password"] {{
  width:100%; padding:14px 16px; border:1.5px solid var(--border);
  border-radius:var(--radius-sm); font-size:15px; background:var(--bg);
  color:var(--text); transition:border-color var(--transition);
}}
.auth-card input:focus {{
  outline:none; border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}}
.auth-card .auth-btn {{
  width:100%; padding:16px; background:var(--btn-primary); color:var(--btn-text);
  border:none; border-radius:var(--radius-sm); font-size:16px; font-weight:600;
  cursor:pointer; transition:all var(--transition);
}}
.auth-card .auth-btn:hover {{ transform:translateY(-2px); opacity:0.92; }}
.auth-card .auth-footer {{
  text-align:center; margin-top:20px; font-size:14px; color:var(--text-muted);
}}
.auth-card .auth-footer a {{ color:var(--primary); font-weight:500; text-decoration:none; }}
.auth-card .auth-footer a:hover {{ text-decoration:underline; }}
.auth-card .auth-divider {{
  display:flex; align-items:center; gap:12px; margin:24px 0; color:var(--text-muted); font-size:13px;
}}
.auth-card .auth-divider::before,
.auth-card .auth-divider::after {{
  content:''; flex:1; height:1px; background:var(--border);
}}
.auth-card .auth-social {{
  display:flex; gap:12px;
}}
.auth-card .auth-social a {{
  flex:1; display:flex; align-items:center; justify-content:center; gap:8px;
  padding:12px; border:1.5px solid var(--border); border-radius:var(--radius-sm);
  text-decoration:none; color:var(--text); font-size:14px; font-weight:500;
  transition:all var(--transition);
}}
.auth-card .auth-social a:hover {{ border-color:var(--primary); background:color-mix(in srgb, var(--primary) 6%, transparent); }}
.auth-checkbox {{ display:flex; align-items:center; gap:8px; font-size:14px; }}
.auth-checkbox input[type="checkbox"] {{ width:16px; height:16px; }}

@media (max-width: 768px) {{
  .about-grid, .contact-grid {{ grid-template-columns:1fr; gap:24px; }}
  .about-stats, .about-values {{ grid-template-columns:1fr; gap:16px; }}
  .about-mission {{ padding:32px 20px; }}
  .newsletter-card {{ flex-direction:column; text-align:center; padding:32px 24px; }}
  .newsletter-form {{ width:100%; }}
  .newsletter-form input {{ width:100%; }}
  .auth-wrapper {{ padding:24px 16px; }}
  .auth-card {{ padding:24px; }}
}}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .nav {{ display:none; }}
  .nav.open {{
    display:flex; flex-direction:column; position:absolute; top:64px; left:0; right:0;
    background:rgba(255,255,255,0.98); backdrop-filter:blur(14px);
    padding:16px 24px; gap:4px; border-bottom:1px solid var(--border);
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
  }}
  .menu-toggle {{ display:flex; }}
  .hero {{ grid-template-columns:1fr; gap:24px; min-height:auto; padding:48px 20px 60px; }}
  .hero-image {{ order:-1; }}
  .hero-image img {{ max-width:300px; }}
  .hero h1 {{ font-size:28px; }}
  .products-grid {{ grid-template-columns:repeat(2,1fr); gap:12px; }}
  .about-teaser, .order-grid, .footer-grid {{ grid-template-columns:1fr; gap:24px; }}
  .reviews-grid, .why-grid {{ grid-template-columns:1fr; gap:16px; }}
  .trust-grid {{ grid-template-columns:repeat(2,1fr); gap:12px; }}
  .footer-grid {{ grid-template-columns:repeat(2,1fr); gap:24px; }}
  .section {{ padding:40px 0; }}
}}
@media (max-width: 480px) {{
  .header {{ height:56px; }}
  .hero {{ min-height:60vh; }}
  .products-grid {{ grid-template-columns:1fr; }}
  .trust-grid {{ grid-template-columns:1fr 1fr; }}
  .hero-actions {{ flex-direction:column; }}
  .hero-actions .btn {{ width:100%; }}
  .footer-grid {{ grid-template-columns:1fr; }}
  .form-row {{ grid-template-columns:1fr; }}
  .order-grid {{ grid-template-columns:1fr; }}
  .checkout-steps {{ flex-wrap:wrap; gap:4px; }}
  .checkout-steps .step {{ flex:1; justify-content:center; padding:8px 12px; font-size:12px; }}
  .cart-item {{ flex-wrap:wrap; gap:8px; }}
  .order-confirm-card {{ padding:32px 20px; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration:0.01ms !important;
    transition-duration:0.01ms !important;
  }}
}}'''


# ── JS Builder (FIX 4) ───────────────────────────────────────────────

def _build_js(phone: str) -> str:
    wa = clean_phone_for_whatsapp(phone)
    return f'''(function() {{
  const toggle = document.getElementById('langToggle');
  if (!toggle) return;
  let currentLang = 'en';
  function setLang(lang) {{
    currentLang = lang;
    toggle.textContent = lang === 'bn' ? 'বাংলা | EN' : 'EN | বাংলা';
    document.documentElement.lang = lang;
    localStorage.setItem('pref_lang', lang);
  }}
  const saved = localStorage.getItem('pref_lang');
  setLang(saved || 'en');
  toggle.addEventListener('click', function(e) {{
    e.stopPropagation();
    setLang(currentLang === 'bn' ? 'en' : 'bn');
  }});
}})();

(function() {{
  const menuBtn = document.getElementById('menuToggle');
  const nav = document.getElementById('mainNav');
  if (!menuBtn || !nav) return;
  menuBtn.addEventListener('click', function() {{
    nav.classList.toggle('open');
    menuBtn.textContent = nav.classList.contains('open') ? '✕' : '☰';
  }});
  document.addEventListener('click', function(e) {{
    if (!nav.contains(e.target) && !menuBtn.contains(e.target)) {{
      nav.classList.remove('open');
      menuBtn.textContent = '☰';
    }}
  }});
  nav.querySelectorAll('a').forEach(l => l.addEventListener('click', function() {{
    nav.classList.remove('open');
    menuBtn.textContent = '☰';
  }}));
}})();

(function() {{
  const header = document.querySelector('.header');
  if (!header) return;
  const observer = new IntersectionObserver(function(e) {{
    header.classList.toggle('scrolled', e[0].boundingClientRect.top < 0);
  }}, {{ threshold: [0, 1] }});
  observer.observe(document.body);
}})();

(function() {{
  const closeBtn = document.querySelector('.announcement-close');
  const bar = document.querySelector('.announcement-bar');
  if (!closeBtn || !bar) return;
  if (localStorage.getItem('announcement_closed')) bar.style.display = 'none';
  closeBtn.addEventListener('click', function() {{
    bar.style.display = 'none';
    localStorage.setItem('announcement_closed', '1');
  }});
}})();

(function() {{
  const filterBtns = document.querySelectorAll('.filter-btn');
  const products = document.querySelectorAll('.product-card');
  if (!filterBtns.length || !products.length) return;
  filterBtns.forEach(btn => {{
    btn.addEventListener('click', function() {{
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const filter = this.dataset.filter?.toLowerCase?.() || '';
      products.forEach(p => {{
        const subcat = p.dataset.subcat?.toLowerCase?.() || '';
        p.style.display = !filter || subcat === filter ? '' : 'none';
      }});
    }});
  }});
  // Trigger initial filter (All) to set correct display state
  const allBtn = document.querySelector('.filter-btn.active');
  if (allBtn) allBtn.click();
}})();

(function() {{
  const params = new URLSearchParams(window.location.search);
  const product = params.get('product');
  if (product) {{
    const select = document.getElementById('orderProduct');
    if (select) {{
      for (let opt of select.options) {{
        if (opt.value === product) {{
          opt.selected = true;
          break;
        }}
      }}
    }}
  }}
  const phone = document.getElementById('orderPhone');
  if (phone) {{
    const savedPhone = localStorage.getItem('order_phone');
    if (savedPhone) phone.value = savedPhone;
    phone.addEventListener('input', function() {{
      localStorage.setItem('order_phone', this.value);
    }});
  }}
  const name = document.getElementById('orderName');
  if (name) {{
    const savedName = localStorage.getItem('order_name');
    if (savedName) name.value = savedName;
    name.addEventListener('input', function() {{
      localStorage.setItem('order_name', this.value);
    }});
  }}
}})();

(function() {{
  const toast = document.createElement('div');
  toast.className = 'toast';
  document.body.appendChild(toast);
  window._showToast = function(msg) {{
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(function() {{ toast.classList.remove('show'); }}, 3500);
  }};
  ['newsletterForm','footerNewsletterForm'].forEach(function(id) {{
    const f = document.getElementById(id);
    if (!f) return;
    f.addEventListener('submit', function(e) {{
      e.preventDefault();
      const input = f.querySelector('input[type="email"]');
      const email = input?.value?.trim();
      if (!email) return;
      input.value = '';
      window._showToast('🎉 Thank you for subscribing!');
    }});
  }});
}})();'''

# ── Index Page (FIX 3) ──────────────────────────────────────────────

def _build_index(name: str, phone: str, canonical: str, address: str,
                  products: List[str], descs: List[str], prices: List[str],
                  services: list, reviews: list, stats: list,
                  trust: list, story_title: str, story_text: str,
                  story_title_bn: str, bengali_name: str,
                  store_type: str, facebook_url: str = '',
                  instagram: str = '') -> str:
    wa = clean_phone_for_whatsapp(phone)
    phone_disp = format_phone_display(phone)
    t = get_design(canonical)
    is_dark = t['bg'] in ('#0d0d0d', '#0f0f0f', '#0a0a0a', '#111111', '#1a1a1a')
    text_color = '#fff' if is_dark else 'var(--text)'
    
    header = _build_header(name, phone, canonical, 'home')

    # 1. Announcement Bar
    announcement = f'''<div class="announcement-bar" id="announcementBar">
  <span class="marquee-wrap">🚚 Free Delivery on Orders Over ৳999 &nbsp;·&nbsp; COD Available Nationwide &nbsp;·&nbsp; Free Returns Within 7 Days &nbsp;·&nbsp; 🚚 Free Delivery on Orders Over ৳999 &nbsp;·&nbsp; COD Available Nationwide &nbsp;·&nbsp; Free Returns Within 7 Days</span>
  <button class="announcement-close" id="announcementClose">✕</button>
</div>'''

    # 2. Hero
    hero_img_src = hero_img_url(canonical)
    hero = f'''<section class="hero">
  <div class="hero-content hero-left">
    <p class="hero-tagline">
      <span class="lang-bn">{CATEGORY_STORE_NAMES.get(canonical, 'store')}</span>
      <span class="lang-en">{CATEGORY_STORE_NAMES.get(canonical, 'store')}</span>
    </p>
    <h1 class="hero-title" style="color:{text_color}">{name}</h1>
    <p class="hero-sub">
      <span class="lang-bn">{address} — সেরা পণ্য, সাশ্রয়ী মূল্যে</span>
      <span class="lang-en">{address} — Best products, affordable prices</span>
    </p>
    <div class="hero-actions">
      <a href="products.html" class="btn btn-primary btn-lg">
        <span class="lang-bn">সব প্রোডাক্ট দেখুন</span>
        <span class="lang-en">Shop Now</span>
      </a>
      <a href="https://wa.me/{wa}" target="_blank" class="btn btn-ghost btn-lg">
        <span class="lang-bn">WhatsApp এ অর্ডার করুন</span>
        <span class="lang-en">Order via WhatsApp</span>
      </a>
    </div>
  </div>
  <div class="hero-image">
    <img src="{hero_img_src}" alt="{name}" class="hero-photo">
  </div>
</section>'''

    # 3. Trust Badges
    trust_html = '\n'.join(
        f'<div class="trust-item"><span class="trust-icon">{t[0]}</span> {t[1]}</div>'
        for t in trust[:4]
    )
    trust_bar = f'''<section class="trust-bar">
  <div class="container trust-grid">
    {trust_html}
  </div>
</section>'''

    # 4. Best Sellers (FIX 7 grid style)
    product_cards = []
    for i, (pname, pdesc, pprice) in enumerate(zip(products, descs, prices)):
        badge_type = "Best Seller" if i % 2 == 0 else "New"
        img = product_img_url(canonical, i)
        encoded = pname.replace(' ', '+')
        card = f'''<div class="product-card">
  <div class="product-img-wrap">
    <img src="{img}" alt="{pname}" loading="lazy">
    <span class="product-badge">{badge_type}</span>
  </div>
  <div class="product-body">
    <h3 class="product-name">{pname}</h3>
    <p class="product-desc">{pdesc}</p>
    <div class="product-price">৳{pprice}</div>
    <div class="product-actions">
      <a href="order.html?product={encoded}" class="btn btn-primary btn-sm">
        <span class="lang-bn">অর্ডার করুন</span>
        <span class="lang-en">Order Now</span>
      </a>
      <a href="https://wa.me/{wa}?text=I%27m%20interested%20in%20{pname}" target="_blank" class="product-wa-btn" aria-label="WhatsApp">{WHATSAPP_SVG}</a>
    </div>
  </div>
</div>'''
        product_cards.append(card)
    
    products_section = f'''<section class="section" id="products">
  <div class="container">
    <div class="section-head">
      <span class="eyebrow">FEATURED</span>
      <h2>
        <span class="lang-bn">বেস্ট সেলার</span>
        <span class="lang-en">Best Sellers</span>
      </h2>
    </div>
    <div class="products-grid">
      {''.join(product_cards[:8])}
    </div>
    <div style="text-align:center;margin-top:32px">
      <a href="products.html" class="btn btn-ghost">
        <span class="lang-bn">সব প্রোডাক্ট দেখুন</span>
        <span class="lang-en">View All Products</span>
      </a>
    </div>
  </div>
</section>'''

    # 5. Brand Story Teaser
    story = f'''<section class="section section-shaded">
  <div class="container">
    <div class="about-teaser">
      <div class="about-teaser-img">
        <img src="https://picsum.photos/seed/{canonical}_story/600/450" alt="{name}" loading="lazy">
      </div>
      <div class="about-teaser-text">
        <h3>
          <span class="lang-bn">{story_title_bn}</span>
          <span class="lang-en">{story_title}</span>
        </h3>
        <p>
          <span class="lang-bn">{story_text}</span>
          <span class="lang-en">{story_text}</span>
        </p>
        <a href="#" class="btn btn-ghost">
          <span class="lang-bn">আরও জানুন →</span>
          <span class="lang-en">Learn More →</span>
        </a>
      </div>
    </div>
  </div>
</section>'''

    # 6. Why Choose Us (3 cards from services)
    why_cards = '\n'.join(
        f'<div class="why-card"><span class="why-icon">{s[0]}</span><h4>{s[1]}</h4><p>{s[2]}</p></div>'
        for s in services[:3]
    )
    why = f'''<section class="section">
  <div class="container">
    <div class="section-head">
      <h2>
        <span class="lang-bn">কেন আমাদের বেছে নেবেন</span>
        <span class="lang-en">Why Choose Us</span>
      </h2>
    </div>
    <div class="why-grid">
      {why_cards}
    </div>
  </div>
</section>'''

    # 7. Social Proof — Reviews
    review_cards = '\n'.join(
        f'''<div class="review-card">
  <div class="review-stars">★★★★★</div>
  <p class="review-text">"{r[2]}"</p>
  <div class="review-author">— {r[0]}</div>
  <div class="review-location">{r[1]}</div>
</div>'''
        for r in reviews[:3]
    )
    reviews_section = f'''<section class="section section-shaded">
  <div class="container">
    <div class="section-head">
      <h2>
        <span class="lang-bn">আমাদের গ্রাহকরা কী বলছেন</span>
        <span class="lang-en">What Our Customers Say</span>
      </h2>
    </div>
    <div class="reviews-grid">
      {review_cards}
    </div>
  </div>
</section>'''

    # 8. Social CTA Banner
    fb = facebook_url if facebook_url else '#'
    social_cta = f'''<section class="social-cta">
  <div class="container">
    <h2>
      <span class="lang-bn">ফেসবুকে ফলো করুন</span>
      <span class="lang-en">Follow us on Facebook</span>
    </h2>
    <p>
      <span class="lang-bn">সর্বশেষ আপডেট ও অফার পেতে আমাদের পেজটি লাইক করুন</span>
      <span class="lang-en">Like our page for the latest updates and offers</span>
    </p>
    <a href="{fb}" target="_blank" class="btn btn-lg">
      <span class="lang-bn">ফেসবুকে ফলো করুন</span>
      <span class="lang-en">Follow on Facebook</span>
    </a>
  </div>
</section>'''

    # 9. Stats bar
    stat_items = '\n'.join(
        f'<div class="stat-card"><span class="stat-icon">{s[0]}</span><div class="stat-val">{s[1]}</div><div class="stat-label">{s[2]}</div></div>'
        for s in stats[:4]
    )
    stats_section = f'''<section class="section stats-section">
  <div class="container">
    <div class="stats-grid">{stat_items}</div>
  </div>
</section>'''

    # 10. Newsletter
    newsletter = f'''<section class="newsletter-section">
  <div class="container">
    <div class="newsletter-card">
      <div class="newsletter-text">
        <h2>
          <span class="lang-bn">আপডেট পেতে সাবস্ক্রাইব করুন</span>
          <span class="lang-en">Subscribe for Updates</span>
        </h2>
        <p>
          <span class="lang-bn">সর্বশেষ প্রোডাক্ট ও এক্সক্লুসিভ অফার জানতে সাবস্ক্রাইব করুন</span>
          <span class="lang-en">Get the latest products and exclusive offers delivered to your inbox</span>
        </p>
      </div>
      <form class="newsletter-form" id="newsletterForm">
        <input type="email" id="newsletterEmail" required
          placeholder="your@email.com"
          aria-label="Email address">
        <button type="submit">
          <span class="lang-bn">সাবস্ক্রাইব</span>
          <span class="lang-en">Subscribe</span>
        </button>
      </form>
    </div>
  </div>
</section>'''

    footer = _build_footer(name, phone, canonical, address,
                           facebook_url, instagram, store_type, bengali_name)
    wa_float = _build_wa_float(phone)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Official Website</title>
  <meta name="description" content="{name} — Premium {store_type} in Bangladesh">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{header}
{announcement}
<main>
{hero}
{trust_bar}
{products_section}
{story}
{why}
{reviews_section}
{social_cta}
</main>
{newsletter}
{footer}
{wa_float}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Products Page (FIX 7) ───────────────────────────────────────────

def _build_products(name: str, phone: str, canonical: str,
                    products: List[str], descs: List[str],
                    prices: List[str], store_type: str,
                    subcats: Optional[List[str]] = None) -> str:
    wa = clean_phone_for_whatsapp(phone)

    header = _build_header(name, phone, canonical, 'products')

    # Use explicit subcategories or extract from product first words
    if subcats and len(subcats) == len(products):
        cat_list = sorted(set(s for s in subcats))
    else:
        cat_list = sorted(set(p.split()[0] if len(p.split()) > 1 else p for p in products))
    filter_pills = '\n'.join(
        f'<button class="filter-btn {"active" if i == 0 else ""}" data-filter="{"" if cat == "All" else cat.lower()}">{cat}</button>'
        for i, cat in enumerate(['All'] + cat_list)
    )

    product_cards = []
    for i, (pname, pdesc, pprice) in enumerate(zip(products, descs, prices)):
        badge_type = "Best Seller" if i % 2 == 0 else "New"
        img = product_img_url(canonical, i)
        encoded = pname.replace(' ', '+')
        subcat = (subcats[i] if subcats and i < len(subcats) else pname.split()[0]).lower()
        card = f'''<div class="product-card" data-subcat="{subcat}">
  <div class="product-img-wrap">
    <img src="{img}" alt="{pname}" loading="lazy">
    <span class="product-badge">{badge_type}</span>
  </div>
  <div class="product-body">
    <h3 class="product-name">{pname}</h3>
    <p class="product-desc">{pdesc}</p>
    <div class="product-price">৳{pprice}</div>
    <div class="product-actions">
      <a href="order.html?product={encoded}" class="btn btn-primary btn-sm">
        <span class="lang-bn">অর্ডার করুন</span>
        <span class="lang-en">Add to Order</span>
      </a>
      <a href="https://wa.me/{wa}?text=I%27m%20interested%20in%20{pname}" target="_blank" class="product-wa-btn">{WHATSAPP_SVG}</a>
    </div>
  </div>
</div>'''
        product_cards.append(card)

    products_grid = '\n'.join(product_cards)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Products — {name}</title>
  <meta name="description" content="Browse our products — {name}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{header}
<main>
  <section class="page-hero">
    <div class="container">
      <h1>
        <span class="lang-bn">আমাদের প্রোডাক্ট</span>
        <span class="lang-en">Our Products</span>
      </h1>
      <p>
        <span class="lang-bn">গুণগত মানের প্রোডাক্ট — সাশ্রয়ী মূল্যে</span>
        <span class="lang-en">Quality products at affordable prices</span>
      </p>
    </div>
  </section>
  <section class="section">
    <div class="container">
      <div class="filter-bar">
        {filter_pills}
      </div>
      <div class="products-grid" id="productsGrid">
        {products_grid}
      </div>
    </div>
  </section>
</main>
{_build_footer(name, phone, canonical, 'Dhaka, Bangladesh', store_type=store_type)}
{_build_wa_float(phone)}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Order Page (FIX 8) ──────────────────────────────────────────────

def _build_order_page(name: str, phone: str, canonical: str,
                      products: List[str], prices: List[str],
                      descs: List[str], store_type: str) -> str:
    wa = clean_phone_for_whatsapp(phone)
    phone_disp = format_phone_display(phone)
    t = get_design(canonical)

    product_options = '\n'.join(
        f'<option value="{p}">{p} — ৳{pr}</option>'
        for p, pr in zip(products, prices)
    )

    header = _build_header(name, phone, canonical, 'order')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Checkout — {name}</title>
  <meta name="description" content="Complete your order — {name}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{header}

<main>
  <section class="page-hero page-hero-sm">
    <div class="container">
      <h1>
        <span class="lang-bn">চেকআউট</span>
        <span class="lang-en">Checkout</span>
      </h1>
      <p>
        <span class="lang-bn">আপনার অর্ডার কনফার্ম করুন</span>
        <span class="lang-en">Complete your order securely</span>
      </p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div id="checkoutApp">
        <div class="checkout-steps">
          <div class="step active" id="step1Indicator"><span class="step-num">1</span> <span class="lang-bn">কার্ট</span><span class="lang-en">Cart</span></div>
          <div class="step" id="step2Indicator"><span class="step-num">2</span> <span class="lang-bn">তথ্য</span><span class="lang-en">Info</span></div>
          <div class="step" id="step3Indicator"><span class="step-num">3</span> <span class="lang-bn">পেমেন্ট</span><span class="lang-en">Payment</span></div>
          <div class="step" id="step4Indicator"><span class="step-num">4</span> <span class="lang-bn">নিশ্চিতকরণ</span><span class="lang-en">Confirm</span></div>
        </div>

        <!-- Step 1: Cart -->
        <div id="step1" class="checkout-step-content">
          <div class="order-grid">
            <div class="order-form-card">
              <h3>
                <span class="lang-bn">আপনার কার্ট</span>
                <span class="lang-en">Your Cart</span>
              </h3>
              <div id="cartItems">
                {''.join(
                  f'''<div class="cart-item" data-product="{p}" data-price="{pr}">
                    <div class="cart-item-img">{p[:2].upper()}</div>
                    <div class="cart-item-body">
                      <div class="cart-item-name">{p}</div>
                      <div class="cart-item-price">\u09F3{pr}</div>
                    </div>
                    <div class="cart-item-qty">
                      <button class="cart-qty-btn" data-action="minus">−</button>
                      <span class="cart-qty-val">1</span>
                      <button class="cart-qty-btn" data-action="plus">+</button>
                    </div>
                    <div class="cart-item-total">৳{pr}</div>
                  </div>'''
                  for p, pr in zip(products, prices)
                )}
              </div>
              <div class="cart-note">
                <label><span class="lang-bn">বিশেষ নির্দেশনা</span><span class="lang-en">Special Note</span></label>
                <textarea id="orderNote" rows="2" placeholder="কোনো বিশেষ নির্দেশনা থাকলে লিখুন..."></textarea>
              </div>
              <button class="submit-btn" id="cartToInfo">
                <span class="lang-bn">চেকআউটে যান</span>
                <span class="lang-en">Proceed to Checkout</span>
              </button>
            </div>

            <div class="order-summary-card">
              <h3>
                <span class="lang-bn">অর্ডার সারাংশ</span>
                <span class="lang-en">Order Summary</span>
              </h3>
              <div id="summaryItems"></div>
              <div class="order-summary-row">
                <span><span class="lang-bn">ডেলিভারি</span><span class="lang-en">Delivery</span></span>
                <span class="summary-value" style="color:#10B981">ফ্রি / Free</span>
              </div>
              <div class="order-summary-total">
                <span><span class="lang-bn">মোট</span><span class="lang-en">Total</span></span>
                <span id="checkoutTotal">৳0</span>
              </div>
              <div class="summary-trust">
                <div class="summary-trust-item">✅ <span class="lang-bn">ক্যাশ অন ডেলিভারি</span><span class="lang-en">Cash on Delivery</span></div>
                <div class="summary-trust-item">🚚 <span class="lang-bn">ফ্রি ডেলিভারি</span><span class="lang-en">Free Delivery</span></div>
                <div class="summary-trust-item">🔒 <span class="lang-bn">নিরাপদ অর্ডার</span><span class="lang-en">Secure Order</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Customer Info -->
        <div id="step2" class="checkout-step-content" style="display:none">
          <div class="order-grid">
            <div class="order-form-card">
              <h3>
                <span class="lang-bn">গ্রাহকের তথ্য</span>
                <span class="lang-en">Customer Information</span>
              </h3>
              <div class="form-group">
                <label><span class="lang-bn">পূর্ণ নাম <span class="required">*</span></span><span class="lang-en">Full Name <span class="required">*</span></span></label>
                <input type="text" id="orderName" required placeholder="আপনার নাম লিখুন">
              </div>
              <div class="form-group">
                <label><span class="lang-bn">ফোন নম্বর <span class="required">*</span></span><span class="lang-en">Phone Number <span class="required">*</span></span></label>
                <input type="tel" id="orderPhone" required placeholder="০১XXX-XXXXXX">
              </div>
              <div class="form-group">
                <label><span class="lang-bn">ডেলিভারি ঠিকানা <span class="required">*</span></span><span class="lang-en">Delivery Address <span class="required">*</span></span></label>
                <textarea id="orderAddress" required rows="3" placeholder="আপনার সম্পূর্ণ ঠিকানা লিখুন"></textarea>
              </div>
              <div class="form-group">
                <label><span class="lang-bn">পেমেন্ট মেথড <span class="required">*</span></span><span class="lang-en">Payment Method <span class="required">*</span></span></label>
                <div class="payment-options" id="paymentOptions">
                  <label class="payment-option">
                    <input type="radio" name="payment" value="COD" checked>
                    <span class="payment-radio"></span>
                    <span class="payment-info">
                      <span class="payment-name"><span class="lang-bn">ক্যাশ অন ডেলিভারি</span><span class="lang-en">Cash on Delivery</span></span>
                      <span class="payment-desc"><span class="lang-bn">পেমেন্ট করুন পণ্য হাতে পেয়ে</span><span class="lang-en">Pay when you receive</span></span>
                    </span>
                  </label>
                  <label class="payment-option">
                    <input type="radio" name="payment" value="bKash">
                    <span class="payment-radio"></span>
                    <span class="payment-info">
                      <span class="payment-name">bKash</span>
                      <span class="payment-desc"><span class="lang-bn">সেন্ড মানি করতে ০১৭১২৩৪৫৬৭৮</span><span class="lang-en">Send money to 01712345678</span></span>
                    </span>
                  </label>
                  <label class="payment-option">
                    <input type="radio" name="payment" value="Nagad">
                    <span class="payment-radio"></span>
                    <span class="payment-info">
                      <span class="payment-name">Nagad</span>
                      <span class="payment-desc"><span class="lang-bn">সেন্ড মানি করতে ০১৭১২৩৪৫৬৭৮</span><span class="lang-en">Send money to 01712345678</span></span>
                    </span>
                  </label>
                </div>
              </div>
              <div class="form-row" style="gap:12px">
                <button class="submit-btn" id="infoBack" style="background:transparent;color:var(--text);border:1.5px solid var(--border)">
                  <span class="lang-bn">পেছনে</span><span class="lang-en">Back</span>
                </button>
                <button class="submit-btn" id="infoToConfirm">
                  <span class="lang-bn">অর্ডার পর্যালোচনা করুন</span><span class="lang-en">Review Order</span>
                </button>
              </div>
            </div>
            <div class="order-summary-card" id="infoSummary"></div>
          </div>
        </div>

        <!-- Step 3: Payment Details -->
        <div id="step3" class="checkout-step-content" style="display:none">
          <div class="order-grid">
            <div class="order-form-card">
              <h3>
                <span class="lang-bn">পেমেন্ট তথ্য</span>
                <span class="lang-en">Payment Details</span>
              </h3>
              <div id="paymentMethodLabel" style="font-size:14px;color:var(--text-muted);margin-bottom:20px"></div>
              <div class="form-group">
                <label><span class="lang-bn">প্রেরকের নম্বর <span class="required">*</span></span><span class="lang-en">Your Sending Number <span class="required">*</span></span></label>
                <input type="tel" id="paySenderNumber" required placeholder="০১XXX-XXXXXX">
              </div>
              <div class="form-group">
                <label><span class="lang-bn">প্রেরিত পরিমাণ (৳) <span class="required">*</span></span><span class="lang-en">Sent Amount (৳) <span class="required">*</span></span></label>
                <input type="number" id="payAmount" required min="1" placeholder="০">
              </div>
              <div class="form-group">
                <label><span class="lang-bn">ট্রানজেকশন আইডি (TrxID) <span class="required">*</span></span><span class="lang-en">Transaction ID <span class="required">*</span></span></label>
                <input type="text" id="payTrxId" required placeholder="TrxID লিখুন">
              </div>
              <div class="form-row" style="gap:12px">
                <button class="submit-btn" id="payBack" style="background:transparent;color:var(--text);border:1.5px solid var(--border)">
                  <span class="lang-bn">পেছনে</span><span class="lang-en">Back</span>
                </button>
                <button class="submit-btn" id="payToConfirm">
                  <span class="lang-bn">অর্ডার কনফার্ম করুন</span><span class="lang-en">Confirm Order</span>
                </button>
              </div>
            </div>
            <div class="order-summary-card" id="paySummary"></div>
          </div>
        </div>

        <!-- Step 4: Confirmation -->
        <div id="step4" class="checkout-step-content" style="display:none">
          <div class="order-confirm-card" id="orderConfirmCard">
            <div class="confirm-icon">✅</div>
            <h2>
              <span class="lang-bn">অর্ডার কনফার্ম হয়েছে!</span>
              <span class="lang-en">Order Confirmed!</span>
            </h2>
            <p class="confirm-subtitle">
              <span class="lang-bn">আপনার অর্ডারটি সফলভাবে গৃহীত হয়েছে। আমরা শীঘ্রই আপনার সাথে যোগাযোগ করব।</span>
              <span class="lang-en">Your order has been placed successfully. We'll contact you shortly.</span>
            </p>
            <div class="confirm-details">
              <div class="confirm-row"><span class="lang-bn">অর্ডার নম্বর</span><span class="lang-en">Order Number</span><span id="confirmOrderNum">#BD-0000</span></div>
              <div class="confirm-row"><span class="lang-bn">নাম</span><span class="lang-en">Name</span><span id="confirmName">—</span></div>
              <div class="confirm-row"><span class="lang-bn">ফোন</span><span class="lang-en">Phone</span><span id="confirmPhone">—</span></div>
              <div class="confirm-row"><span class="lang-bn">ঠিকানা</span><span class="lang-en">Address</span><span id="confirmAddress">—</span></div>
              <div class="confirm-row"><span class="lang-bn">পেমেন্ট</span><span class="lang-en">Payment</span><span id="confirmPayment">—</span></div>
              <div class="confirm-row"><span class="lang-bn">মোট</span><span class="lang-en">Total</span><span id="confirmTotal">—</span></div>
            </div>
            <div id="confirmItems" class="confirm-items"></div>
            <p class="confirm-message" id="confirmMessage">
              <span class="lang-bn">আপনাকে ধন্যবাদ! আপনার অর্ডারটি প্রক্রিয়াকরণ করা হবে।</span>
              <span class="lang-en">Thank you! Your order will be processed.</span>
            </p>
            <a href="/" class="submit-btn" style="display:inline-block;text-align:center;text-decoration:none;margin-top:16px">
              <span class="lang-bn">হোমপেজে ফিরে যান</span>
              <span class="lang-en">Back to Home</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</main>

{_build_footer(name, phone, canonical, 'Dhaka, Bangladesh', store_type=store_type)}
{_build_wa_float(phone)}

<script>
(function() {{
  const prices = {{ {','.join(f'"{p}":{pr}' for p, pr in zip(products, prices))} }};

  // Pre-select product from URL param
  const urlParams = new URLSearchParams(window.location.search);
  const preselected = urlParams.get('product');

  function getQty(el) {{ return parseInt(el.querySelector('.cart-qty-val').textContent) || 1; }}
  function setQty(el, q) {{ el.querySelector('.cart-qty-val').textContent = q; updateTotals(); }}

  function getPayment() {{
    const sel = document.querySelector('input[name="payment"]:checked');
    return sel ? sel.value : 'COD';
  }}

  function updateTotals() {{
    let total = 0;
    const items = [];
    document.querySelectorAll('.cart-item').forEach(function(el) {{
      if (el.style.display === 'none') return;
      const p = el.dataset.product;
      const pr = parseFloat(el.dataset.price) || 0;
      const q = getQty(el);
      const t = pr * q;
      total += t;
      items.push({{ name: p, price: pr, qty: q, total: t }});
    }});
    document.getElementById('checkoutTotal').textContent = '৳' + total;
    const sb = document.getElementById('summaryItems');
    if (sb) sb.innerHTML = items.map(function(i) {{
      return '<div class="order-summary-row"><span>' + i.name + ' × ' + i.qty + '</span><span>৳' + i.total + '</span></div>';
    }}).join('');
    return items;
  }}

  // Handle pre-selected product from URL
  if (preselected) {{
    document.querySelectorAll('.cart-item').forEach(function(el) {{
      if (el.dataset.product !== preselected) {{
        el.style.display = 'none';
      }} else {{
        setQty(el, 1);
      }}
    }});
  }}

  document.querySelectorAll('.cart-qty-btn').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      const item = this.closest('.cart-item');
      if (!item) return;
      let q = getQty(item);
      if (this.dataset.action === 'plus') {{ q = Math.min(q + 1, 99); }}
      else {{ q = Math.max(q - 1, 0); }}
      if (q === 0) {{ item.remove(); }}
      else {{ setQty(item, q); }}
      updateTotals();
    }});
  }});

  function showStep(n) {{
    document.querySelectorAll('.checkout-step-content').forEach(function(el,i) {{
      el.style.display = (i+1 === n) ? 'block' : 'none';
    }});
    for (var i = 1; i <= 4; i++) {{
      var ind = document.getElementById('step' + i + 'Indicator');
      if (ind) ind.classList.toggle('active', i === n);
    }}
    if (n === 1) updateTotals();
  }}

  function updateSummarySidebar(targetId, items, total) {{
    var sb = document.getElementById(targetId);
    if (!sb) return;
    var html = '<h3 style="font-family:var(--font-heading);font-size:18px;font-weight:700;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)"><span class=\"lang-bn\">অর্ডার সারাংশ</span><span class=\"lang-en\">Order Summary</span></h3>';
    items.forEach(function(i) {{ html += '<div class=\"order-summary-row\"><span>' + i.name + ' × ' + i.qty + '</span><span>৳' + i.total + '</span></div>'; }});
    html += '<div class=\"order-summary-row\"><span><span class=\"lang-bn\">ডেলিভারি</span><span class=\"lang-en\">Delivery</span></span><span style=\"color:#10B981\">ফ্রি / Free</span></div>';
    html += '<div class=\"order-summary-total\"><span><span class=\"lang-bn\">মোট</span><span class=\"lang-en\">Total</span></span><span>৳' + total + '</span></div>';
    sb.innerHTML = html;
  }}

  document.getElementById('cartToInfo').addEventListener('click', function() {{
    var items = updateTotals();
    if (!items.length) {{ alert('Your cart is empty.'); return; }}
    var total = 0; items.forEach(function(i) {{ total += i.total; }});
    updateSummarySidebar('infoSummary', items, total);
    showStep(2);
  }});

  document.getElementById('infoBack').addEventListener('click', function() {{ showStep(1); }});

  document.getElementById('infoToConfirm').addEventListener('click', function() {{
    var name = document.getElementById('orderName')?.value?.trim();
    var phone = document.getElementById('orderPhone')?.value?.trim();
    var address = document.getElementById('orderAddress')?.value?.trim();
    if (!name || !phone || !address) {{ alert('Please fill in all required fields.'); return; }}

    var payment = getPayment();
    var items = updateTotals();
    var total = 0; items.forEach(function(i) {{ total += i.total; }});

    if (payment === 'COD') {{
      // COD skips payment details, go straight to confirmation
      placeOrder(name, phone, address, payment, 'Cash on Delivery', '', total, items);
    }} else {{
      // bKash/Nagad — show payment details step
      var label = document.getElementById('paymentMethodLabel');
      if (label) label.innerHTML = '<span class=\"lang-bn\">আপনি <strong>' + payment + '</strong> সিলেক্ট করেছেন। নিচের তথ্য দিন:</span><span class=\"lang-en\">You selected <strong>' + payment + '</strong>. Fill in the details below:</span>';
      // Pre-fill amount
      var amt = document.getElementById('payAmount');
      if (amt) amt.value = total;
      updateSummarySidebar('paySummary', items, total);
      showStep(3);
    }}
  }});

  document.getElementById('payBack').addEventListener('click', function() {{ showStep(2); }});

  document.getElementById('payToConfirm').addEventListener('click', function() {{
    var sender = document.getElementById('paySenderNumber')?.value?.trim();
    var amount = document.getElementById('payAmount')?.value?.trim();
    var trxId = document.getElementById('payTrxId')?.value?.trim();
    if (!sender || !amount || !trxId) {{ alert('Please fill in all payment details.'); return; }}

    var payment = getPayment();
    var name = document.getElementById('orderName')?.value?.trim();
    var phone = document.getElementById('orderPhone')?.value?.trim();
    var address = document.getElementById('orderAddress')?.value?.trim();
    var items = updateTotals();
    var total = 0; items.forEach(function(i) {{ total += i.total; }});

    placeOrder(name, phone, address, payment, payment + ' (Trx: ' + trxId + ')', sender + ', Trx: ' + trxId, total, items);
  }});

  function placeOrder(name, phone, address, payment, paymentLabel, payDetail, total, items) {{
    var orderNum = '#BD-' + String(Date.now()).slice(-6);
    document.getElementById('confirmOrderNum').textContent = orderNum;
    document.getElementById('confirmName').textContent = name;
    document.getElementById('confirmPhone').textContent = phone;
    document.getElementById('confirmAddress').textContent = address;
    document.getElementById('confirmPayment').textContent = paymentLabel;
    document.getElementById('confirmTotal').textContent = '৳' + total;

    var ci = document.getElementById('confirmItems');
    if (ci) ci.innerHTML = items.map(function(i) {{
      return '<div class=\"confirm-item\"><span>' + i.name + ' × ' + i.qty + '</span><span>৳' + i.total + '</span></div>';
    }}).join('');

    showStep(4);

    var msg = '🛍 NEW ORDER\\n📋 Order: ' + orderNum + '\\n👤 ' + name + '\\n📞 ' + phone + '\\n📍 ' + address;
    items.forEach(function(i) {{ msg += '\\n🛒 ' + i.name + ' × ' + i.qty + ' = ৳' + i.total; }});
    msg += '\\n💳 Payment: ' + paymentLabel;
    if (payDetail) msg += '\\n🔢 ' + payDetail;
    msg += '\\n💰 Total: ৳' + total;
  }}

  updateTotals();
}})();
</script>
<script src="script.js"></script>
</body>
</html>'''

    return html


# ── About Page ────────────────────────────────────────────────────────

def _build_about(name: str, phone: str, canonical: str, address: str,
                 store_type: str, bengali_name: str,
                 facebook_url: str = '', instagram: str = '') -> str:
    t = get_design(canonical)
    is_dark = t['bg'] in ('#0d0d0d', '#0f0f0f', '#0a0a0a', '#111111', '#1a1a1a')
    text_color = '#fff' if is_dark else 'var(--text)'

    stories = {
        "fashion": ("Style Meets Tradition", "Bella-BD started with a simple vision: bring the finest fashion to every woman in Bangladesh. From our small boutique in Gulshan, we've grown to serve thousands of customers nationwide, always prioritizing quality, fit, and elegance.", "We believe fashion is more than clothing — it's confidence. Every piece in our collection is handpicked for its craftsmanship, fabric quality, and timeless appeal."),
        "jewelry": ("Crafted with Love", "Our journey began with a passion for authentic jewelry. Each piece tells a story of heritage, craftsmanship, and timeless beauty. We source the finest materials to bring you jewelry that lasts a lifetime.", "We believe every woman deserves to feel radiant. Our collections are designed to celebrate your unique beauty, from everyday elegance to special occasion glamour."),
        "skincare": ("Glow Naturally", "Bella-BD Skincare was born from a desire to make premium skincare accessible in Bangladesh. We partner with trusted laboratories to bring science-backed formulas that deliver real results.", "Healthy skin is happy skin. We're committed to clean, cruelty-free formulations that nourish your skin and boost your confidence naturally."),
        "baby": ("Caring for Little Ones", "Every product in our baby collection is selected with the utmost care. From organic fabrics to BPA-free feeding essentials, we prioritize safety, comfort, and quality for your little ones.", "We believe babies deserve the best. Our mission is to make parenting easier by offering safe, premium, and affordable baby products."),
        "home": ("Make Your House a Home", "Your home is your sanctuary. We curate home essentials that blend functionality with beauty — from elegant dinnerware to smart storage solutions that transform your living space.", "We believe great design starts at home. Every product we offer is chosen to bring comfort, style, and joy to your everyday life."),
        "restaurant": ("A Taste of Excellence", "Our restaurant partners serve dishes crafted with passion and the finest ingredients. From family feasts to intimate dinners, we bring restaurant-quality dining to your table.", "Good food brings people together. We're on a mission to make exceptional dining accessible to every family in Bangladesh."),
        "beauty": ("Beauty Redefined", "Bella-BD Beauty brings you the best of global beauty trends. From K-beauty inspired skincare to professional-grade makeup, we help you look and feel your best.", "Beauty is for everyone. We believe in inclusivity, quality, and innovation — making premium beauty products accessible across Bangladesh."),
        "general": ("Our Story", "Bella-BD started with a dream: to make quality products accessible to everyone. Today we serve thousands of happy customers across Bangladesh with a commitment to excellence.", "Quality, trust, and customer satisfaction are at the heart of everything we do. We're not just a store — we're your trusted shopping partner."),
    }
    story = stories.get(canonical, stories['general'])

    stats_data = CATEGORY_STAT_ITEMS.get(canonical, CATEGORY_STAT_ITEMS['general'])
    stat_cards = '\n'.join(
        f'<div class="about-stat"><span class="stat-icon">{s[0]}</span>'
        f'<div class="stat-val">{s[1]}</div>'
        f'<div class="stat-label">{s[2]}</div></div>'
        for s in stats_data[:3]
    )

    values = [
        ("🎯", "Quality First", "Every product meets our strict quality standards before reaching you."),
        ("🤝", "Trust & Transparency", "Honest pricing, genuine products, and clear communication always."),
        ("🚚", "Customer First", "Free delivery, easy returns, and 24/7 support via WhatsApp."),
    ]
    value_cards = '\n'.join(
        f'<div class="value-card"><span class="value-icon">{v[0]}</span>'
        f'<h3>{v[1]}</h3><p>{v[2]}</p></div>'
        for v in values
    )

    hero_img = hero_img_url(canonical)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About Us — {name}</title>
  <meta name="description" content="Learn about {name} — our story, mission, and values">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{_build_header(name, phone, canonical, 'about')}

<main>
  <section class="page-hero">
    <div class="container">
      <h1>
        <span class="lang-bn">আমাদের সম্পর্কে</span>
        <span class="lang-en">About Us</span>
      </h1>
      <p>
        <span class="lang-bn">{name} — আপনার বিশ্বস্ত অনলাইন গন্তব্য</span>
        <span class="lang-en">{name} — Your trusted online destination</span>
      </p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="about-grid">
        <div class="about-story">
          <h2>{story[0]}</h2>
          <p>{story[1]}</p>
          <p>{story[2]}</p>
          <div class="about-stats">{stat_cards}</div>
        </div>
        <div class="hero-image"><img src="{hero_img}" alt="{name}" class="hero-photo"></div>
      </div>
    </div>
  </section>

  <section class="section section-shaded">
    <div class="container">
      <div class="about-mission">
        <h2>
          <span class="lang-bn">আমাদের লক্ষ্য</span>
          <span class="lang-en">Our Mission</span>
        </h2>
        <p>
          <span class="lang-bn">আমাদের লক্ষ্য হলো বাংলাদেশের প্রতিটি ঘরে গুণগত মানের পণ্য পৌঁছে দেওয়া, সাশ্রয়ী মূল্যে এবং বিশ্বস্ত সেবার সাথে।</span>
          <span class="lang-en">Our mission is to deliver quality products to every home in Bangladesh, at affordable prices with trusted service.</span>
        </p>
      </div>
      <div class="about-values">{value_cards}</div>
    </div>
  </section>

  <section class="section">
    <div class="container" style="text-align:center">
      <h2 style="font-family:var(--font-heading);font-size:24px;margin-bottom:16px">
        <span class="lang-bn">আমাদের সাথে যোগাযোগ করুন</span>
        <span class="lang-en">Get in Touch</span>
      </h2>
      <p style="color:var(--text-muted);margin-bottom:24px;max-width:500px;margin-left:auto;margin-right:auto">
        <span class="lang-bn">আপনার প্রশ্ন বা মতামত জানাতে চাইলে আমাদের সাথে যোগাযোগ করুন</span>
        <span class="lang-en">Have a question or feedback? We'd love to hear from you</span>
      </p>
      <a href="contact.html" class="btn btn-primary btn-lg">
        <span class="lang-bn">যোগাযোগ করুন</span>
        <span class="lang-en">Contact Us</span>
      </a>
    </div>
  </section>
</main>

{_build_footer(name, phone, canonical, address, facebook_url, instagram, store_type, bengali_name)}
{_build_wa_float(phone)}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Contact Page ──────────────────────────────────────────────────────

def _build_contact(name: str, phone: str, canonical: str, address: str,
                   store_type: str, bengali_name: str,
                   facebook_url: str = '', instagram: str = '') -> str:
    phone_disp = format_phone_display(phone)
    wa = clean_phone_for_whatsapp(phone)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contact Us — {name}</title>
  <meta name="description" content="Get in touch with {name} — we're here to help">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{_build_header(name, phone, canonical, 'contact')}

<main>
  <section class="page-hero">
    <div class="container">
      <h1>
        <span class="lang-bn">যোগাযোগ</span>
        <span class="lang-en">Contact Us</span>
      </h1>
      <p>
        <span class="lang-bn">আমরা আপনার কথা শুনতে চাই</span>
        <span class="lang-en">We'd love to hear from you</span>
      </p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="contact-grid">
        <div class="contact-info-card">
          <h2>
            <span class="lang-bn">আমাদের ঠিকানা</span>
            <span class="lang-en">Our Information</span>
          </h2>
          <div class="contact-item">
            <span class="ci-icon">📍</span>
            <div><div class="ci-label"><span class="lang-bn">ঠিকানা</span><span class="lang-en">Address</span></div><div class="ci-value">{address}</div></div>
          </div>
          <div class="contact-item">
            <span class="ci-icon">📞</span>
            <div><div class="ci-label"><span class="lang-bn">ফোন</span><span class="lang-en">Phone</span></div><div class="ci-value"><a href="tel:{phone_disp}" style="color:var(--primary);text-decoration:none">{phone_disp}</a></div></div>
          </div>
          <div class="contact-item">
            <span class="ci-icon">💬</span>
            <div><div class="ci-label">WhatsApp</div><div class="ci-value"><a href="https://wa.me/{wa}" target="_blank" style="color:var(--primary);text-decoration:none">Chat with us</a></div></div>
          </div>
          <div class="contact-item">
            <span class="ci-icon">🕐</span>
            <div><div class="ci-label"><span class="lang-bn">ব্যবসায়িক সময়</span><span class="lang-en">Business Hours</span></div><div class="ci-value"><span class="lang-bn">শনি-বৃহস্পতি: ৯AM-৯PM</span><span class="lang-en">Sat-Thu: 9AM-9PM</span></div></div>
          </div>
          <div class="contact-item">
            <span class="ci-icon">📅</span>
            <div><div class="ci-label"><span class="lang-bn">সাপ্তাহিক ছুটি</span><span class="lang-en">Weekly Holiday</span></div><div class="ci-value" style="color:#EF4444"><span class="lang-bn">শুক্রবার</span><span class="lang-en">Friday</span></div></div>
          </div>
          <div class="contact-map-placeholder">
            <span class="lang-bn">📍 গুগল ম্যাপে দেখুন</span>
            <span class="lang-en">📍 View on Google Maps</span>
          </div>
        </div>

        <div class="contact-form-card">
          <h2>
            <span class="lang-bn">মেসেজ পাঠান</span>
            <span class="lang-en">Send us a Message</span>
          </h2>
          <form id="contactForm">
            <div class="form-group">
              <label><span class="lang-bn">আপনার নাম <span class="required">*</span></span><span class="lang-en">Your Name <span class="required">*</span></span></label>
              <input type="text" id="contactName" required placeholder="আপনার নাম লিখুন">
            </div>
            <div class="form-group">
              <label><span class="lang-bn">ইমেইল</span><span class="lang-en">Email</span></label>
              <input type="email" id="contactEmail" placeholder="your@email.com">
            </div>
            <div class="form-group">
              <label><span class="lang-bn">ফোন নম্বর <span class="required">*</span></span><span class="lang-en">Phone Number <span class="required">*</span></span></label>
              <input type="tel" id="contactPhone" required placeholder="০১XXX-XXXXXX">
            </div>
            <div class="form-group">
              <label><span class="lang-bn">বিষয়</span><span class="lang-en">Subject</span></label>
              <select id="contactSubject">
                <option value="general"><span class="lang-bn">সাধারণ জিজ্ঞাসা</span><span class="lang-en">General Inquiry</span></option>
                <option value="order"><span class="lang-bn">অর্ডার সংক্রান্ত</span><span class="lang-en">Order Related</span></option>
                <option value="return"><span class="lang-bn">রিটার্ন / রিফান্ড</span><span class="lang-en">Return / Refund</span></option>
                <option value="feedback"><span class="lang-bn">মতামত</span><span class="lang-en">Feedback</span></option>
                <option value="other"><span class="lang-bn">অন্যান্য</span><span class="lang-en">Other</span></option>
              </select>
            </div>
            <div class="form-group">
              <label><span class="lang-bn">মেসেজ <span class="required">*</span></span><span class="lang-en">Message <span class="required">*</span></span></label>
              <textarea id="contactMessage" required rows="4" placeholder="আপনার মেসেজ লিখুন..."></textarea>
            </div>
            <button type="submit" class="submit-btn">
              <span class="lang-bn">WhatsApp এ মেসেজ পাঠান</span>
              <span class="lang-en">Send via WhatsApp</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </section>
</main>

{_build_footer(name, phone, canonical, address, facebook_url, instagram, store_type, bengali_name)}
{_build_wa_float(phone)}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Login Page ────────────────────────────────────────────────────────

def _build_login(name: str, phone: str, canonical: str) -> str:
    wa = clean_phone_for_whatsapp(phone)
    t = get_design(canonical)
    bg_light = t['bg'] if t['bg'] != '#0d0d0d' else '#f8f8fc'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login — {name}</title>
  <meta name="description" content="Login to your {name} account">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{_build_header(name, phone, canonical, 'login')}

<main class="auth-wrapper">
  <div class="auth-card">
    <h1>
      <span class="lang-bn">সাইন ইন</span>
      <span class="lang-en">Sign In</span>
    </h1>
    <p class="auth-subtitle">
      <span class="lang-bn">আপনার অ্যাকাউন্টে লগইন করুন</span>
      <span class="lang-en">Welcome back! Sign in to your account</span>
    </p>
    <form id="loginForm">
      <div class="form-group">
        <label><span class="lang-bn">ইমেইল বা ফোন নম্বর <span class="required">*</span></span><span class="lang-en">Email or Phone <span class="required">*</span></span></label>
        <input type="text" id="loginEmail" required placeholder="your@email.com বা ০১XXX-XXXXXX">
      </div>
      <div class="form-group">
        <label><span class="lang-bn">পাসওয়ার্ড <span class="required">*</span></span><span class="lang-en">Password <span class="required">*</span></span></label>
        <input type="password" id="loginPassword" required placeholder="••••••••">
      </div>
      <div class="form-group" style="display:flex;justify-content:space-between;align-items:center">
        <label class="auth-checkbox">
          <input type="checkbox" checked>
          <span class="lang-bn">মনে রাখুন</span><span class="lang-en">Remember me</span>
        </label>
        <a href="#" style="color:var(--primary);font-size:14px;text-decoration:none">
          <span class="lang-bn">পাসওয়ার্ড ভুলে গেছেন?</span>
          <span class="lang-en">Forgot password?</span>
        </a>
      </div>
      <button type="submit" class="auth-btn">
        <span class="lang-bn">সাইন ইন</span>
        <span class="lang-en">Sign In</span>
      </button>
    </form>
    <div class="auth-divider">
      <span><span class="lang-bn">অথবা</span><span class="lang-en">Or</span></span>
    </div>
    <div class="auth-social">
      <a href="https://wa.me/{wa}" target="_blank">
        <span>💬</span> <span class="lang-bn">WhatsApp</span><span class="lang-en">WhatsApp</span>
      </a>
      <a href="#">
        <span>📧</span> <span class="lang-bn">ইমেইল</span><span class="lang-en">Email</span>
      </a>
    </div>
    <div class="auth-footer">
      <span class="lang-bn">নতুন গ্রাহক?</span><span class="lang-en">New customer?</span>
      <a href="register.html">
        <span class="lang-bn">রেজিস্টার করুন</span><span class="lang-en">Create Account</span>
      </a>
    </div>
  </div>
</main>

{_build_footer(name, phone, canonical, 'Dhaka, Bangladesh', store_type='store')}
{_build_wa_float(phone)}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Register Page ─────────────────────────────────────────────────────

def _build_register(name: str, phone: str, canonical: str) -> str:
    wa = clean_phone_for_whatsapp(phone)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Create Account — {name}</title>
  <meta name="description" content="Create your {name} account">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
{_build_header(name, phone, canonical, 'register')}

<main class="auth-wrapper">
  <div class="auth-card">
    <h1>
      <span class="lang-bn">নতুন অ্যাকাউন্ট</span>
      <span class="lang-en">Create Account</span>
    </h1>
    <p class="auth-subtitle">
      <span class="lang-bn">রেজিস্টার করে শুরু করুন</span>
      <span class="lang-en">Register and start shopping</span>
    </p>
    <form id="registerForm">
      <div class="form-group">
        <label><span class="lang-bn">পূর্ণ নাম <span class="required">*</span></span><span class="lang-en">Full Name <span class="required">*</span></span></label>
        <input type="text" id="regName" required placeholder="আপনার নাম লিখুন">
      </div>
      <div class="form-group">
        <label><span class="lang-bn">ইমেইল</span><span class="lang-en">Email</span></label>
        <input type="email" id="regEmail" placeholder="your@email.com">
      </div>
      <div class="form-group">
        <label><span class="lang-bn">ফোন নম্বর <span class="required">*</span></span><span class="lang-en">Phone Number <span class="required">*</span></span></label>
        <input type="tel" id="regPhone" required placeholder="০১XXX-XXXXXX">
      </div>
      <div class="form-group">
        <label><span class="lang-bn">পাসওয়ার্ড <span class="required">*</span></span><span class="lang-en">Password <span class="required">*</span></span></label>
        <input type="password" id="regPassword" required placeholder="কমপক্ষে ৬ অক্ষর">
      </div>
      <div class="form-group">
        <label><span class="lang-bn">পাসওয়ার্ড নিশ্চিত করুন <span class="required">*</span></span><span class="lang-en">Confirm Password <span class="required">*</span></span></label>
        <input type="password" id="regConfirm" required placeholder="পুনরায় পাসওয়ার্ড লিখুন">
      </div>
      <div class="form-group">
        <label class="auth-checkbox">
          <input type="checkbox" required>
          <span class="lang-bn">আমি শর্তাবলী এবং গোপনীয়তা নীতিতে সম্মতি জানাচ্ছি</span>
          <span class="lang-en">I agree to the Terms & Conditions and Privacy Policy</span>
        </label>
      </div>
      <button type="submit" class="auth-btn">
        <span class="lang-bn">অ্যাকাউন্ট তৈরি করুন</span>
        <span class="lang-en">Create Account</span>
      </button>
    </form>
    <div class="auth-divider">
      <span><span class="lang-bn">অথবা</span><span class="lang-en">Or</span></span>
    </div>
    <div class="auth-social">
      <a href="https://wa.me/{wa}" target="_blank">
        <span>💬</span> <span class="lang-bn">WhatsApp দিয়ে রেজিস্টার</span><span class="lang-en">Register via WhatsApp</span>
      </a>
    </div>
    <div class="auth-footer">
      <span class="lang-bn">ইতিমধ্যে অ্যাকাউন্ট আছে?</span><span class="lang-en">Already have an account?</span>
      <a href="login.html">
        <span class="lang-bn">সাইন ইন করুন</span><span class="lang-en">Sign In</span>
      </a>
    </div>
  </div>
</main>

{_build_footer(name, phone, canonical, 'Dhaka, Bangladesh', store_type='store')}
{_build_wa_float(phone)}
<script src="script.js"></script>
</body>
</html>'''
    return html


# ── Main Generator ────────────────────────────────────────────────────

def generate_site(out_dir: str, name: str, phone: str, canonical: str,
                  address: str = 'Dhaka, Bangladesh',
                  facebook_url: str = '', instagram: str = '',
                  services: Optional[list] = None,
                  reviews: Optional[list] = None,
                  primary_color: Optional[str] = None,
                  accent_color: Optional[str] = None) -> None:
    """Generate complete multi-page site into out_dir."""
    products = CATEGORY_PRODUCTS.get(canonical, CATEGORY_PRODUCTS['general'])
    descs = CATEGORY_PRODUCT_DESCS.get(canonical, CATEGORY_PRODUCT_DESCS['general'])
    prices = CATEGORY_PRODUCT_PRICES.get(canonical, CATEGORY_PRODUCT_PRICES['general'])
    stats = CATEGORY_STAT_ITEMS.get(canonical, CATEGORY_STAT_ITEMS['general'])
    trust = CATEGORY_TRUST_ITEMS.get(canonical, CATEGORY_TRUST_ITEMS['general'])
    store_type = CATEGORY_STORE_NAMES.get(canonical, 'store')
    bengali_name = CATEGORY_BENGALI_NAMES.get(canonical, 'জেনারেল')
    story_title = CATEGORY_STORY_TITLE.get(canonical, 'Our Story')
    story_text = CATEGORY_STORY_TEXT.get(canonical, 'Committed to excellence.')
    story_title_bn = CATEGORY_ABOUT_TITLE_BN.get(canonical, 'আমাদের গল্প')

    if services is None:
        services_cfg = {
            "fashion": [("👗", "Trendy Collection", "Latest fashion trends with quality fabrics"), ("🚚", "Fast Delivery", "Free delivery across Bangladesh"), ("🔄", "Easy Return", "Hassle-free returns within 7 days")],
            "jewelry": [("💍", "Premium Designs", "Handcrafted jewelry with authentic materials"), ("🎁", "Gift Wrapping", "Beautiful complimentary gift wrapping"), ("✅", "Certified", "Hallmarked and certified genuine")],
            "skincare": [("🧴", "Premium Formulas", "Science-backed skincare for radiant skin"), ("🧪", "Dermatologist Tested", "Safe for all skin types"), ("🚚", "Free Delivery", "Free shipping on all orders")],
            "baby": [("👶", "Baby Safe", "All products meet safety standards"), ("🧸", "Premium Quality", "Soft, safe, and durable materials"), ("🚚", "Fast Delivery", "Quick delivery across Bangladesh")],
            "home": [("🏠", "Premium Quality", "Durable home essentials for everyday use"), ("📦", "Smart Storage", "Space-saving organization solutions"), ("🚚", "Free Delivery", "Free shipping on orders over ৳999")],
            "restaurant": [("🍽️", "Chef Specials", "Crafted by expert chefs with fresh ingredients"), ("🚚", "Home Delivery", "Hot, fresh meals delivered to your door"), ("🎉", "Event Catering", "Full-service catering for any occasion")],
            "beauty": [("💇", "Expert Products", "Premium beauty products for every need"), ("💄", "Trendy Styles", "Stay on trend with our curated collection"), ("📦", "Fast Shipping", "Quick delivery across the country")],
            "retail": [("🛍️", "Curated Collection", "Carefully selected products for you"), ("🚚", "Free Delivery", "Free shipping on all orders"), ("💳", "COD Available", "Pay when you receive")],
            "general": [("⭐", "Quality Service", "Professional service you can rely on"), ("🚚", "Fast Delivery", "Timely delivery every time"), ("💳", "COD", "Cash on delivery available")],
        }
        services = services_cfg.get(canonical, services_cfg['general'])

    if reviews is None:
        reviews_cfg = {
            "fashion": [("Fatima Begum", "Gulshan", "Amazing quality and fit! The kameez I ordered was perfect. Will definitely shop again."), ("Rafiq Hasan", "Banani", "Great collection of panjabi. The fabric quality is outstanding and the tailoring is precise."), ("Sadia Rahman", "Mirpur", "Ordered sarees for a wedding and they were absolutely beautiful. Fast delivery too!")],
            "jewelry": [("Nusrat Jahan", "Dhanmondi", "The necklace set is stunning! Pure gold and exactly as described. Very happy with my purchase."), ("Tahmina Akhter", "Uttara", "Beautiful bangles at great prices. The craftsmanship is excellent. Highly recommended!"), ("Shahana Parvin", "Gulshan", "I bought an anklet and it's gorgeous. The design is unique and the gold quality is authentic.")],
            "skincare": [("Kamal Hossain", "Motijheel", "The Vitamin C serum transformed my skin. Visible results in just 2 weeks. Amazing product!"), ("Jasmine Akhter", "Khilgaon", "I love the sunscreen SPF50. It's lightweight and doesn't leave white cast. Perfect for daily use."), ("Shahidul Islam", "Bashundhara", "The face wash is gentle yet effective. My acne has reduced significantly. Great product!")],
            "baby": [("Ayesha Siddiqua", "Mohakhali", "The baby bodysuits are so soft and gentle on my baby's skin. Love the quality!"), ("Mamunur Rashid", "Baridhara", "Feeding bottles are BPA-free and very durable. My baby took to them immediately."), ("Farzana Islam", "Niketan", "Diapers are super absorbent and comfortable. Best we've tried so far!")],
            "home": [("Abdul Karim", "Malibagh", "The ceramic dinner set is elegant and high quality. Looks beautiful on the dining table."), ("Shamima Nasrin", "Wari", "Storage organizers helped me declutter my kitchen. Very practical and well-made."), ("Jahangir Alam", "Shantibagh", "Bedsheet set is super soft and the print is gorgeous. Excellent value for money!")],
            "beauty": [("Nusrat Jahan", "Dhanmondi", "Absolutely love the lipstick set! The shades are perfect and long-lasting. Highly recommended!"), ("Tahmina Akhter", "Uttara", "The Vitamin C serum gave my skin a natural glow. Results are visible within days."), ("Shahana Parvin", "Gulshan", "Best beauty products in Bangladesh! The quality is amazing and prices are very reasonable.")],
        }
        reviews = reviews_cfg.get(canonical, [
            ("Farzana Islam", "Dhaka", "Great service! They truly care about their customers and deliver excellent quality."),
            ("Mizanur Rahman", "Gulshan", "Very professional and reliable. They exceeded my expectations in every way."),
            ("Nasima Khatun", "Uttara", "Been a loyal customer for years. Consistent quality and friendly service."),
        ])

    os.makedirs(out_dir, exist_ok=True)

    css = _build_css(canonical, primary_color, accent_color)
    js = _build_js(phone)

    with open(os.path.join(out_dir, 'styles.css'), 'w', encoding='utf-8') as f:
        f.write(css)
    with open(os.path.join(out_dir, 'script.js'), 'w', encoding='utf-8') as f:
        f.write(js)

    index = _build_index(name, phone, canonical, address,
                         products, descs, prices,
                         services, reviews, stats, trust,
                         story_title, story_text, story_title_bn,
                         bengali_name, store_type, facebook_url, instagram)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index)
    print(f"  index.html ✓")

    products_page = _build_products(name, phone, canonical,
                                    products, descs, prices, store_type,
                                    CATEGORY_PRODUCT_SUBCATS.get(canonical))
    with open(os.path.join(out_dir, 'products.html'), 'w', encoding='utf-8') as f:
        f.write(products_page)
    print(f"  products.html ✓")

    order_page = _build_order_page(name, phone, canonical,
                                   products, prices, descs, store_type)
    with open(os.path.join(out_dir, 'order.html'), 'w', encoding='utf-8') as f:
        f.write(order_page)
    print(f"  order.html ✓")

    about = _build_about(name, phone, canonical, address,
                         store_type, bengali_name, facebook_url, instagram)
    with open(os.path.join(out_dir, 'about.html'), 'w', encoding='utf-8') as f:
        f.write(about)
    print(f"  about.html ✓")

    contact = _build_contact(name, phone, canonical, address,
                             store_type, bengali_name, facebook_url, instagram)
    with open(os.path.join(out_dir, 'contact.html'), 'w', encoding='utf-8') as f:
        f.write(contact)
    print(f"  contact.html ✓")

    login = _build_login(name, phone, canonical)
    with open(os.path.join(out_dir, 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login)
    print(f"  login.html ✓")

    register = _build_register(name, phone, canonical)
    with open(os.path.join(out_dir, 'register.html'), 'w', encoding='utf-8') as f:
        f.write(register)
    print(f"  register.html ✓")

    print(f"  styles.css ✓")
    print(f"  script.js ✓")


def main():
    parser = argparse.ArgumentParser(description='Generate Shopify-style demo site')
    parser.add_argument('--name', required=True, help='Business name')
    parser.add_argument('--phone', required=True, help='Phone number')
    parser.add_argument('--category', required=True, help='Business category')
    parser.add_argument('--address', default='Dhaka, Bangladesh', help='Business address')
    parser.add_argument('--out', required=True, help='Output directory')
    parser.add_argument('--facebook', default='', help='Facebook page URL or handle')
    parser.add_argument('--instagram', default='', help='Instagram handle')
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'demo'))
    try:
        from category_lib import classify_category
        canonical = classify_category(args.category)
    except ImportError:
        canonical = args.category.lower().replace(' ', '_')

    print(f"Generating site for: {args.name}")
    print(f"  Category: {args.category} → canonical: {canonical}")
    print(f"  Output:   {args.out}")

    generate_site(
        out_dir=args.out,
        name=args.name,
        phone=args.phone,
        canonical=canonical,
        address=args.address,
        facebook_url=args.facebook,
        instagram=args.instagram,
    )


if __name__ == '__main__':
    main()
