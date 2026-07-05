# template_config.py \u2014 Per-category template configuration
# Each category has: accent palette, service cards, about copy, pain points,
# Trojan Horse strategy, pricing, taglines, and icons.

from typing import Dict, Any, List, Tuple

# \u2500\u2500 Hero Taglines \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
TAGLINES: Dict[str, str] = {
    "restaurant":    "Where Every Meal Becomes a Memory",
    "beauty":        "Unveil Your Most Confident Self",
    "retail":        "Quality Products, Exceptional Experience",
    "education":     "Empowering Minds, Building Futures",
    "healthcare":    "Your Health Is Our Sole Priority",
    "pharmacy":      "Trusted Care, Right at Your Doorstep",
    "fitness":       "Transform Your Body, Elevate Your Life",
    "automotive":    "Precision Service That Keeps You Moving",
    "manufacturing": "Built with Precision. Delivered with Pride.",
    "agriculture":   "Growing Quality, Harvesting Trust",
    "hotel":         "Where Comfort Meets Genuine Care",
    "realestate":    "Find the Space Where Your Story Begins",
    "services":      "Professional Service, Personal Touch",
    "general":       "Quality Service You Can Trust",
}

# \u2500\u2500 Hero Badge Labels \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
HERO_BADGES: Dict[str, str] = {
    "restaurant":    "PREMIUM DINING",
    "beauty":        "LUXURY SALON",
    "retail":        "PREMIUM STORE",
    "education":     "LEARNING CENTER",
    "healthcare":    "HEALTHCARE PROVIDER",
    "pharmacy":      "PHARMACY CARE",
    "fitness":       "FITNESS CENTER",
    "automotive":    "AUTO SERVICE",
    "manufacturing": "MANUFACTURER",
    "agriculture":   "AGRO BUSINESS",
    "hotel":         "HOSPITALITY",
    "realestate":    "REAL ESTATE",
    "services":      "SERVICE PROVIDER",
    "general":       "LOCAL BUSINESS",
}

# \u2500\u2500 Category Icons \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
CATEGORY_ICONS: Dict[str, str] = {
    "restaurant":    "\U0001F37D\uFE0F",
    "beauty":        "\U0001F487",
    "retail":        "\U0001F6CD\uFE0F",
    "education":     "\U0001F4DA",
    "healthcare":    "\U0001FA7A",
    "pharmacy":      "\U0001F48A",
    "fitness":       "\U0001F4AA",
    "automotive":    "\U0001F527",
    "manufacturing": "\U0001F3ED",
    "agriculture":   "\U0001F33E",
    "hotel":         "\U0001F3E8",
    "realestate":    "\U0001F3E0",
    "services":      "\u2B50",
    "general":       "\u2B50",
}

# \u2500\u2500 About Us Copy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Each entry is (heading, paragraph1, paragraph2)
ABOUT_COPY: Dict[str, Tuple[str, str, str]] = {
    "restaurant": (
        "Fresh Ingredients, Authentic Taste",
        "Every dish we serve is crafted with the freshest ingredients sourced daily. "
        "Our chefs bring years of culinary expertise to create flavors that keep "
        "customers coming back for more. From traditional favorites to innovative "
        "creations, every plate tells a story of quality and passion.",
        "Located in the heart of the community, we take pride in being your go-to "
        "destination for exceptional dining. Whether it's a quick lunch, a family "
        "dinner, or a special celebration \u2014 we make every meal memorable.",
    ),
    "beauty": (
        "Expert Care, Personalized Beauty",
        "We believe every person deserves to look and feel their absolute best. "
        "Our team of skilled stylists and beauty professionals brings years of "
        "experience, using premium products and the latest techniques to deliver "
        "results that exceed expectations.",
        "From precision haircuts and vibrant coloring to rejuvenating facials and "
        "bridal makeovers \u2014 we provide a complete beauty experience tailored to "
        "your unique style and preferences.",
    ),
    "retail": (
        "Curated Quality, Every Day",
        "We carefully select every product on our shelves to ensure you get the "
        "best quality at fair prices. Our team is passionate about what we do, "
        "and it shows in the variety and freshness of our inventory.",
        "Whether you're shopping for daily essentials or something special, you'll "
        "find a welcoming environment and helpful staff ready to assist. "
        "Your satisfaction is the measure of our success.",
    ),
    "education": (
        "Learning That Transforms Lives",
        "We are committed to providing quality education that prepares students for "
        "real-world success. Our experienced faculty, modern facilities, and proven "
        "curriculum create an environment where every learner can thrive.",
        "From foundational skills to advanced certification, we guide each student "
        "on a personalized learning journey. Our track record of student success "
        "speaks for itself \u2014 join a community dedicated to excellence.",
    ),
    "healthcare": (
        "Compassionate Care, Advanced Medicine",
        "We combine modern medical technology with genuine human care. Our team of "
        "experienced healthcare professionals is dedicated to accurate diagnosis, "
        "effective treatment, and compassionate patient support at every step.",
        "Your health journey matters to us. We invest in the latest diagnostic "
        "equipment, maintain rigorous quality standards, and ensure every patient "
        "receives the attention and respect they deserve.",
    ),
    "pharmacy": (
        "Your Health Partner, Always Available",
        "We stock a comprehensive range of quality medicines, health supplements, "
        "and wellness products. Our knowledgeable pharmacists provide expert guidance "
        "on prescriptions, dosage, and health management.",
        "With fast, reliable service and genuine care for every customer, we've "
        "become the trusted pharmacy choice for families in our community. "
        "Your well-being is our priority \u2014 every single day.",
    ),
    "fitness": (
        "Stronger Every Day",
        "We provide a complete fitness environment with modern equipment, expert "
        "trainers, and a motivating community. Whether your goal is weight loss, "
        "muscle building, or overall wellness \u2014 we have the tools and guidance "
        "to get you there.",
        "Join group classes, work with a personal trainer, or train independently \u2014 "
        "our flexible approach means you can work out your way. Every rep, every "
        "session, every goal \u2014 we're with you.",
    ),
    "automotive": (
        "Expert Care for Your Vehicle",
        "We bring precision, experience, and honest service to every vehicle we touch. "
        "From routine maintenance to complex repairs, our certified mechanics use "
        "modern diagnostic tools and quality parts to keep you safely on the road.",
        "We understand that your vehicle is essential to your daily life. That's why "
        "we work efficiently without compromising quality, and we always explain what "
        "needs to be done \u2014 no surprises, just reliable service.",
    ),
    "manufacturing": (
        "Quality Manufacturing, Reliable Delivery",
        "Our modern facility combines precision machinery with skilled craftsmanship "
        "to produce goods that meet the highest standards. Every product that leaves "
        "our floor undergoes rigorous quality control at multiple checkpoints.",
        "We partner with businesses of all sizes, offering flexible production volumes, "
        "competitive pricing, and reliable delivery schedules. Your specifications, "
        "our expertise \u2014 a partnership built on quality.",
    ),
    "agriculture": (
        "From Our Farm to Your Table",
        "We are committed to sustainable farming practices that produce the freshest, "
        "healthiest products while caring for the land. Our integrated approach "
        "combines traditional farming wisdom with modern agricultural science.",
        "Quality begins at the source. Every harvest is tested, graded, and handled "
        "with care to ensure it reaches you at peak freshness. We supply individuals, "
        "retailers, and wholesalers with consistent, premium-quality produce.",
    ),
    "hotel": (
        "Your Comfort Is Our Mission",
        "We believe a stay should be more than just a room \u2014 it should be an experience "
        "of genuine hospitality. From the moment you arrive, our team is dedicated to "
        "making your stay comfortable, convenient, and memorable.",
        "With well-appointed rooms, thoughtful amenities, and a prime location, we "
        "provide the perfect base for business travelers, tourists, and families. "
        "Come as a guest, leave as a friend.",
    ),
    "realestate": (
        "Turning Spaces into Homes",
        "We bring integrity, market expertise, and personalized service to every "
        "property transaction. Whether you're buying your first home, investing in "
        "commercial property, or selling \u2014 we guide you through every step.",
        "Our deep knowledge of the local market means we can find opportunities others "
        "miss. We don't just show properties; we help you make informed decisions "
        "that align with your goals and budget.",
    ),
    "services": (
        "Reliable Service, Every Time",
        "We take pride in delivering professional service with a personal touch. "
        "Our skilled team arrives on time, works efficiently, and ensures the job "
        "is done right \u2014 the first time.",
        "Quality workmanship, transparent pricing, and genuine care for our customers "
        "have earned us the trust of the community. When you need it done right, "
        "you know who to call.",
    ),
    "general": (
        "Committed to Excellence",
        "We are dedicated to delivering exceptional quality and service to every "
        "customer. Your satisfaction is our priority, and we strive to exceed "
        "expectations every step of the way.",
        "Visit us today and experience the difference. Located in the heart of the "
        "community, we pride ourselves on being a trusted name that our customers "
        "can rely on.",
    ),
}

# \u2500\u2500 Service Cards \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# (icon_emoji, title, description)
SERVICE_ITEMS: Dict[str, List[Tuple[str, str, str]]] = {
    "restaurant": [
        ("\U0001F37D\uFE0F", "Dine-In Experience",
         "Enjoy a warm, inviting atmosphere with chef-crafted dishes made from the freshest ingredients"),
        ("\U0001F6F5", "Home Delivery",
         "Hot, fresh meals delivered to your doorstep \u2014 fast, reliable, and delicious"),
        ("\U0001F389", "Event Catering",
         "Full-service catering for parties, corporate events, weddings, and special occasions"),
    ],
    "beauty": [
        ("\U0001F487", "Hair Styling",
         "Precision cuts, expert coloring, and custom styling tailored to your personality"),
        ("\U0001F485", "Nail Art & Care",
         "Trendy manicures, pedicures, and artistic nail designs using premium products"),
        ("\u2728", "Facial & Skincare",
         "Rejuvenating facials, deep cleansing, and personalized skincare treatments"),
    ],
    "retail": [
        ("\U0001F6CD\uFE0F", "In-Store Shopping",
         "Browse our curated collection in a clean, organized, and welcoming environment"),
        ("\U0001F69A", "Home Delivery",
         "Fast, free delivery within the area \u2014 shop from home with confidence"),
        ("\U0001F381", "Gift Wrapping",
         "Beautiful complimentary gift wrapping for every purchase \u2014 perfect for any occasion"),
    ],
    "education": [
        ("\U0001F4DA", "Expert Faculty",
         "Learn from experienced, qualified instructors passionate about student success"),
        ("\U0001F4BB", "Modern Labs",
         "State-of-the-art computer and science labs for hands-on practical learning"),
        ("\U0001F3C6", "Certification",
         "Recognized certificates upon successful completion \u2014 valued by employers"),
    ],
    "healthcare": [
        ("\U0001FA7A", "Expert Consultation",
         "Thorough medical advice from experienced, compassionate practitioners"),
        ("\U0001F52C", "Advanced Diagnostics",
         "Modern diagnostic equipment delivering fast, accurate results"),
        ("\U0001F48A", "Pharmacy Service",
         "Full-service pharmacy with prescription support and health counseling"),
    ],
    "pharmacy": [
        ("\U0001F48A", "Prescription Fulfillment",
         "Quick and accurate dispensing with expert pharmacist consultation"),
        ("\U0001FA79", "Health Products",
         "Comprehensive range of wellness products, supplements, and medical supplies"),
        ("\U0001F69A", "Free Home Delivery",
         "Medication delivered to your doorstep \u2014 reliable and on time"),
    ],
    "fitness": [
        ("\U0001F4AA", "Modern Equipment",
         "Full range of cardio and strength equipment for every fitness level"),
        ("\U0001F9D8", "Group Classes",
         "Yoga, Zumba, HIIT, spinning, and more \u2014 led by certified instructors"),
        ("\U0001F957", "Nutrition Guidance",
         "Personalized diet plans and nutrition counseling to complement your training"),
    ],
    "automotive": [
        ("\U0001F527", "Expert Repairs",
         "Skilled mechanical repairs for all vehicle makes and models"),
        ("\U0001F6E0\uFE0F", "Tire Service",
         "New tires, wheel alignment, rotation, and balancing \u2014 all in one place"),
        ("\U0001F50D", "Full Inspection",
         "Comprehensive vehicle inspection and diagnostics using advanced tools"),
    ],
    "manufacturing": [
        ("\U0001F3ED", "Modern Production",
         "Precision manufacturing with state-of-the-art machinery and quality materials"),
        ("\u2705", "Quality Control",
         "Rigorous multi-stage testing ensures every product meets exact specifications"),
        ("\U0001F4E6", "Bulk Fulfillment",
         "Flexible volume production with reliable delivery schedules for wholesale partners"),
    ],
    "agriculture": [
        ("\U0001F33E", "Fresh Produce",
         "Farm-fresh fruits, vegetables, and grains harvested at peak quality"),
        ("\U0001F69C", "Bulk Supply",
         "Reliable supply chain for wholesalers, retailers, and food processors"),
        ("\U0001F9EA", "Quality Testing",
         "Rigorous quality checks and grading before every shipment leaves the farm"),
    ],
    "hotel": [
        ("\U0001F6CF\uFE0F", "Comfort Rooms",
         "Well-appointed, clean rooms with modern amenities for a restful stay"),
        ("\U0001F373", "Complimentary Breakfast",
         "Start your day with a fresh, delicious breakfast \u2014 included with your stay"),
        ("\U0001F4F6", "Free High-Speed WiFi",
         "Stay connected with reliable high-speed internet throughout the property"),
    ],
    "realestate": [
        ("\U0001F3E0", "Property Listings",
         "Curated selection of residential and commercial properties across prime locations"),
        ("\U0001F4CB", "Property Management",
         "End-to-end management for landlords \u2014 tenants, maintenance, and rent collection"),
        ("\U0001F91D", "Expert Consultation",
         "Personalized advice on buying, selling, and investing in real estate"),
    ],
    "services": [
        ("\u2B50", "Quality Workmanship",
         "Professional-grade service delivered with precision and attention to detail"),
        ("\U0001F91D", "Customer First",
         "Your satisfaction drives everything we do \u2014 transparent, honest, reliable"),
        ("\U0001F680", "Fast & Reliable",
         "We respect your time \u2014 prompt service without compromising on quality"),
    ],
    "general": [
        ("\u2B50", "Quality Service",
         "Professional service you can rely on \u2014 every time"),
        ("\U0001F91D", "Customer First",
         "Your satisfaction is our top priority \u2014 we're not happy until you are"),
        ("\U0001F680", "Fast & Reliable",
         "Timely delivery of every service we offer \u2014 no delays, no excuses"),
    ],
}

# \u2500\u2500 Stats (years, clients, rating) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# \u2500\u2500 Process Steps (How It Works) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# 3 steps: (title, description)
PROCESS_STEPS: Dict[str, List[Tuple[str, str]]] = {
    "restaurant": [
        ("Browse Our Menu", "Explore our carefully crafted menu featuring fresh, locally sourced ingredients and chef specialties."),
        ("Place Your Order", "Call us, order online, or visit us in person. We make it easy to enjoy great food."),
        ("Savor Every Bite", "Freshly prepared meals served with care. Dine in, take away, or get it delivered."),
    ],
    "beauty": [
        ("Book Your Session", "Select your service and preferred time. Walk-ins welcome, appointments recommended."),
        ("Enjoy Your Treatment", "Relax in our salon while our experts pamper you with premium products."),
        ("Walk Out Radiant", "Leave feeling refreshed, confident, and beautiful. We guarantee you'll love the results."),
    ],
    "retail": [
        ("Browse Our Collection", "Explore our carefully curated selection of quality products at great prices."),
        ("Shop Your Way", "Visit our store, call us, or order online for fast home delivery."),
        ("Enjoy Your Purchase", "Quality products backed by our satisfaction guarantee and friendly support."),
    ],
    "education": [
        ("Explore Programs", "Discover our range of courses designed to build real-world skills."),
        ("Enroll Online", "Simple admission process with guidance from our friendly team."),
        ("Start Learning", "Begin your journey with expert faculty and modern learning resources."),
    ],
    "healthcare": [
        ("Book Appointment", "Schedule a consultation online or by phone. Same-day appointments available."),
        ("Get Diagnosed", "Modern diagnostic equipment and thorough examination by experienced doctors."),
        ("Start Treatment", "Personalized treatment plan with ongoing support and follow-up care."),
    ],
    "pharmacy": [
        ("Consult Our Pharmacist", "Speak with our expert pharmacists for professional health advice."),
        ("Get Your Medicine", "Fast, accurate prescription fulfillment with quality-assured products."),
        ("Free Home Delivery", "Medication delivered to your doorstep. Reliable, discreet, and on time."),
    ],
    "fitness": [
        ("Choose Your Plan", "Select from flexible membership options that fit your schedule and goals."),
        ("Train Smart", "Access modern equipment, group classes, and certified personal trainers."),
        ("See Results", "Track your progress, stay motivated, and achieve your fitness goals."),
    ],
    "automotive": [
        ("Book a Service", "Schedule your appointment online or by phone. Free vehicle inspection included."),
        ("Expert Diagnostics", "Advanced diagnostic equipment identifies issues accurately the first time."),
        ("Drive with Confidence", "Quality repairs backed by warranty. Your vehicle is in safe hands."),
    ],
    "manufacturing": [
        ("Share Your Requirements", "Send us your specifications, volume needs, and quality requirements."),
        ("Quality Production", "Precision manufacturing with multi-stage quality control at every step."),
        ("On-Time Delivery", "Reliable fulfillment with real-time order tracking and flexible logistics."),
    ],
    "agriculture": [
        ("Sustainable Farming", "Modern agricultural practices combined with traditional expertise."),
        ("Quality Harvesting", "Carefully harvested, graded, and tested for consistent premium quality."),
        ("Fresh Delivery", "From farm to table \u2014 delivered at peak freshness to customers and partners."),
    ],
    "hotel": [
        ("Book Your Stay", "Easy online booking or call us. Best rates guaranteed when you book direct."),
        ("Check In & Relax", "Smooth check-in, comfortable rooms, and thoughtful amenities await you."),
        ("Enjoy Your Visit", "Explore the area, enjoy complimentary breakfast, and make lasting memories."),
    ],
    "realestate": [
        ("Browse Properties", "Explore our curated listings of prime residential and commercial properties."),
        ("Schedule a Visit", "Book a tour of properties that match your needs and budget."),
        ("Close with Confidence", "Expert guidance through negotiations, paperwork, and final settlement."),
    ],
    "services": [
        ("Contact Us", "Reach out by phone, WhatsApp, or visit us. Free consultation and quote."),
        ("We Take Action", "Our skilled team gets to work promptly with professional-grade tools and techniques."),
        ("Job Done Right", "Completed to your satisfaction with quality workmanship and clean finish."),
    ],
    "general": [
        ("Reach Out", "Contact us by phone, WhatsApp, or visit in person. We're always happy to help."),
        ("We Deliver", "Professional service with attention to detail and genuine care for your needs."),
        ("You're Satisfied", "Your satisfaction is our priority. We don't rest until you're happy."),
    ],
}

# \u2500\u2500 Reviews \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# 3 reviews per category: (name, location, quote)
REVIEWS: Dict[str, List[Tuple[str, str, str]]] = {
    "restaurant": [
        ("Fatima Begum", "Gulshan", "The quality of food here is remarkable. We ordered for a family dinner and everyone was impressed. The delivery was quick and the portions were generous."),
        ("Rafiq Hasan", "Banani", "Best biryani in town! I've been coming here for years and the taste never changes. The staff is friendly and the atmosphere is welcoming."),
        ("Sadia Rahman", "Mirpur", "Ordered for a corporate event and they handled everything perfectly. Great presentation, delicious food, and timely delivery. Highly recommended!"),
    ],
    "beauty": [
        ("Nusrat Jahan", "Dhanmondi", "Absolutely love this salon! The stylists really listen to what you want. My haircut turned out exactly as I envisioned. The ambiance is so relaxing too."),
        ("Tahmina Akhter", "Uttara", "I got my bridal makeup done here and it was perfect. The team was professional, punctual, and the makeup lasted all day without any touch-ups needed."),
        ("Shahana Parvin", "Gulshan", "Been coming here for facials for over a year now. My skin has never looked better. The products they use are premium and the results show."),
    ],
    "retail": [
        ("Kamal Hossain", "Motijheel", "Great shopping experience. The store is well-organized and the staff is helpful without being pushy. Found exactly what I needed at a fair price."),
        ("Jasmine Akhter", "Khilgaon", "I love the home delivery service. Ordered some household items and they arrived within hours. Quality was excellent and well-packaged."),
        ("Shahidul Islam", "Bashundhara", "Their gift wrapping service is amazing! Bought presents for my whole family and each one was beautifully wrapped. Will definitely shop here again."),
    ],
    "education": [
        ("Ayesha Siddiqua", "Mohakhali", "The teachers here genuinely care about student progress. My daughter's confidence has grown so much since joining. The facilities are excellent too."),
        ("Mamunur Rashid", "Baridhara", "Completed my professional certification here. The curriculum was practical and up-to-date. Got a job offer within weeks of graduating. Truly life-changing."),
        ("Farzana Islam", "Niketan", "The lab facilities are outstanding. My son gets hands-on experience that goes beyond textbooks. The regular progress updates keep parents informed and involved."),
    ],
    "healthcare": [
        ("Abdul Karim", "Malibagh", "I've been a patient here for years. The doctors are thorough and take time to explain everything. The diagnostic equipment is modern and results come quickly."),
        ("Shamima Nasrin", "Wari", "Had a great experience with the gynecology department. The female doctor made me feel comfortable and the entire process was smooth. Highly recommend."),
        ("Jahangir Alam", "Shantibagh", "Brought my father for a full health checkup. The staff was courteous, the tests were comprehensive, and the report was detailed. Excellent service overall."),
    ],
    "pharmacy": [
        ("Rokeya Begum", "Mirpur 10", "They have every medicine I've ever needed. The pharmacist always explains the dosage carefully and suggests alternatives when something is out of stock."),
        ("Ismail Hossain", "Mohammadpur", "The free home delivery is a lifesaver for my elderly mother. We call and they deliver within hours. Always genuine products with proper expiry dates."),
        ("Farida Yasmin", "Pallabi", "Very professional and well-stocked pharmacy. The staff is knowledgeable about both allopathic and herbal options. I trust them completely with my family's health."),
    ],
    "fitness": [
        ("Arman Hossain", "Gulshan 2", "Best gym in the area! The equipment is modern and well-maintained. Trainers are encouraging and actually care about your form and progress."),
        ("Sajeda Parvin", "Banani", "Zumba classes are so much fun! The instructor keeps us motivated and the community is very supportive. Lost 12 kg in 4 months. Feeling amazing!"),
        ("Tanvir Ahmed", "Bashundhara", "The nutrition guidance has been a game-changer for me. Combined with the workout plans, I've seen real results. Great value for the membership fee."),
    ],
    "automotive": [
        ("Hasan Mahmud", "Tejgaon", "Reasonable prices and honest work. They could have charged me for unnecessary repairs but they didn't. My car has been running smoothly since the service."),
        ("Mizanur Rahman", "Kakrail", "Got my AC fixed and the entire engine checked. The mechanics are skilled and explained everything clearly. Finished on time and within the quoted price."),
        ("Sifat Jahan", "Moghbazar", "Quick tire replacement and alignment service. The team was efficient and I was back on the road in under an hour. Will definitely come back for future services."),
    ],
    "manufacturing": [
        ("Rafiqul Islam", "Savar", "We've been sourcing components from this manufacturer for 2 years. Consistent quality, competitive pricing, and they always meet delivery deadlines."),
        ("Shahin Ahmed", "Gazipur", "Excellent production capabilities. They handled our large order with precision and the quality control was impressive. A reliable partner for our business."),
        ("Nasrin Akhter", "Narayanganj", "The attention to detail in their products is outstanding. Every batch meets our specifications perfectly. Communication is smooth and professional."),
    ],
    "agriculture": [
        ("Abdur Rahim", "Kishoreganj", "Best quality rice I've sourced in years. The moisture content is always perfect and the grading is consistent. My buyers are very satisfied."),
        ("Shahana Begum", "Mymensingh", "The vegetables arrive fresh and well-packed. We have a standing order for our restaurant chain and they've never disappointed on quality or quantity."),
        ("Fazlul Karim", "Comilla", "Started with a small order to test quality, now we're buying bulk every month. Fair pricing, honest weights, and genuine products. A trustworthy supplier."),
    ],
    "hotel": [
        ("Tariq Hasan", "Business Traveler", "Excellent stay! The rooms are clean, well-appointed, and the WiFi is fast. Breakfast had good variety and the staff went out of their way to help."),
        ("Sadia Islam", "Family Vacation", "The family room was spacious and kids loved the service. Location is perfect for exploring the city. Will definitely stay here again on our next visit."),
        ("Kamruzzaman", "Couple Getaway", "Romantic ambiance and thoughtful amenities. The staff arranged a special dinner for us and it was wonderful. Great value for a premium experience."),
    ],
    "realestate": [
        ("Azizul Haque", "Bashundhara", "Found my dream apartment through them. The agent was patient, showed us multiple options, and negotiated a fair price. Professional and trustworthy service."),
        ("Sharmin Akhter", "Uttara", "Sold my property within 2 weeks at a great price. The team handled all the paperwork and marketing. Made a stressful process feel effortless."),
        ("Javed Karim", "Gulshan", "Excellent property management service. They found quality tenants quickly and handle all maintenance issues promptly. Best decision I made for my investment."),
    ],
    "services": [
        ("Imran Hossain", "Mirpur DOHS", "Called them for an emergency plumbing issue. They arrived within 30 minutes, fixed the problem quickly, and the pricing was transparent. Highly reliable."),
        ("Tahmina Akhter", "Baridhara", "Used their cleaning service for my office. Professional team, thorough work, and they used proper equipment. My office has never looked this clean."),
        ("Shahid Ullah", "Niketan", "Excellent electrical work. The electrician was skilled, safety-conscious, and cleaned up after the job. Fair pricing for the quality of work delivered."),
    ],
    "general": [
        ("Farzana Islam", "Dhaka", "Great service from a local business that truly cares. They went above and beyond to help me. I highly recommend them to everyone I know."),
        ("Mizanur Rahman", "Gulshan", "Very professional and reliable. They delivered exactly what they promised, on time and within budget. A refreshing experience in today's market."),
        ("Nasima Khatun", "Uttara", "Been a loyal customer for years and they've never disappointed. Quality service, fair prices, and friendly staff. The kind of business every community needs."),
    ],
}

STATS_MAP: Dict[str, Tuple[str, str, str]] = {
    "restaurant":    ("10+", "4.8", "500+"),
    "beauty":        ("8+", "4.8", "300+"),
    "retail":        ("12+", "4.7", "700+"),
    "education":     ("15+", "4.8", "800+"),
    "healthcare":    ("20+", "4.9", "1000+"),
    "pharmacy":      ("12+", "4.8", "500+"),
    "fitness":       ("7+", "4.8", "400+"),
    "automotive":    ("18+", "4.7", "600+"),
    "manufacturing": ("25+", "4.8", "300+"),
    "agriculture":   ("30+", "4.7", "200+"),
    "hotel":         ("15+", "4.7", "500+"),
    "realestate":    ("10+", "4.8", "300+"),
    "services":      ("10+", "4.8", "400+"),
    "general":       ("10+", "4.8", "400+"),
}

# \u2500\u2500 Helper: get config for a category \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def get_config(canonical: str) -> Dict[str, Any]:
    """Return full configuration dict for a canonical category."""
    return {
        "tagline": TAGLINES.get(canonical, TAGLINES["general"]),
        "hero_badge": HERO_BADGES.get(canonical, HERO_BADGES["general"]),
        "icon": CATEGORY_ICONS.get(canonical, CATEGORY_ICONS["general"]),
        "about": ABOUT_COPY.get(canonical, ABOUT_COPY["general"]),
        "services": SERVICE_ITEMS.get(canonical, SERVICE_ITEMS["general"]),
        "stats": STATS_MAP.get(canonical, STATS_MAP["general"]),
        "process": PROCESS_STEPS.get(canonical, PROCESS_STEPS["general"]),
        "reviews": REVIEWS.get(canonical, REVIEWS["general"]),
    }
