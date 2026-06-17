"""
Generate 500 diverse personas for the SynthPanel usability-testing library.

Run:  python generate_personas.py
Output: synthpanel/persona/library/examples.yaml
"""

from __future__ import annotations

import random
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Seed for reproducibility
# ---------------------------------------------------------------------------
random.seed(42)

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
OUT = Path(__file__).parent / "synthpanel/persona/library/examples.yaml"

# ---------------------------------------------------------------------------
# Controlled vocabulary helpers
# ---------------------------------------------------------------------------
GENDERS = ["F", "M", "nonbinary", "undisclosed"]
GENDER_WEIGHTS = [0.44, 0.44, 0.08, 0.04]

AGE_BANDS = ["13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]

CITY_TIERS = ["metro", "small_city", "rural"]
CITY_WEIGHTS = [0.50, 0.30, 0.20]

EDUCATIONS = ["none", "primary", "highschool", "college", "graduate"]

DEVICES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.55, 0.35, 0.10]

OS_BY_DEVICE = {
    "mobile": (["android", "ios"], [0.65, 0.35]),
    "desktop": (["windows", "macos", "linux"], [0.60, 0.30, 0.10]),
    "tablet": (["android", "ios"], [0.55, 0.45]),
}

NETWORKS = ["fast", "slow_4g", "3g_throttled"]
NETWORK_WEIGHTS = [0.45, 0.35, 0.20]

A11Y_POOL = ["screen_reader", "low_vision", "large_text", "color_blind", "motor"]

PATIENCE_VALS = ["low", "medium", "high"]
EXPLORATION_VALS = ["skimmer", "methodical", "goal_driven"]
READS_INSTR = ["low", "medium", "high"]
DECISION_SPEEDS = ["impulsive", "deliberate"]

PRIVACY_VALS = ["low", "medium", "high"]
PRICE_VALS = ["low", "medium", "high"]
TECH_ADOPTION_VALS = ["early_adopter", "mainstream", "laggard"]

CONTEXTS = ["first_visit", "returning", "from_ad", "referred"]
TIME_PRESSURES = ["relaxed", "normal", "rushed"]

# ---------------------------------------------------------------------------
# Names by region/culture
# ---------------------------------------------------------------------------

KOREAN_FEMALE_NAMES = [
    "김순자", "이영희", "박지현", "최수연", "정미영", "한소희", "윤아름",
    "강은주", "조민지", "신유리", "임채원", "오세은", "류나영", "배소연",
    "노지은", "서현아", "문수지", "남가을", "홍지연", "권나연",
]
KOREAN_MALE_NAMES = [
    "김민준", "이준호", "박성훈", "최재원", "정도윤", "한승우", "윤태양",
    "강동현", "조민석", "신현우", "임재훈", "오정민", "류태성", "배진호",
    "노재현", "서민준", "문대성", "남기현", "홍승우", "권민호",
]
KOREAN_NB_NAMES = ["이현진", "김지민", "박다인", "최성현"]

JAPANESE_FEMALE_NAMES = [
    "田中花子", "鈴木さくら", "佐藤美咲", "山田陽子", "中村優花",
    "小林麻衣", "加藤奈緒", "伊藤彩香", "渡辺恵", "高橋理沙",
]
JAPANESE_MALE_NAMES = [
    "田中太郎", "鈴木一郎", "佐藤健", "山田浩二", "中村翔",
    "小林誠", "加藤拓也", "伊藤大輝", "渡辺隼人", "高橋勇",
]

CHINESE_FEMALE_NAMES = [
    "王芳", "李娜", "张慧", "刘欣", "陈雪", "杨婷", "赵梦",
    "黄丽", "周静", "吴燕",
]
CHINESE_MALE_NAMES = [
    "王伟", "李明", "张强", "刘洋", "陈磊", "杨帆", "赵鑫",
    "黄浩", "周健", "吴军",
]

INDIAN_FEMALE_NAMES = [
    "Priya Nair", "Anjali Sharma", "Divya Menon", "Sunita Patel",
    "Kavya Reddy", "Meera Iyer", "Deepa Krishnan", "Riya Singh",
    "Pooja Gupta", "Ananya Pillai", "Swati Rao", "Nikita Joshi",
    "Shreya Bose", "Nisha Verma", "Lavanya Murthy",
]
INDIAN_MALE_NAMES = [
    "Rahul Verma", "Amit Kumar", "Vikram Singh", "Suresh Patel",
    "Rohit Sharma", "Arjun Nair", "Kiran Reddy", "Manoj Iyer",
    "Sanjay Gupta", "Naveen Krishnan", "Arun Pillai", "Rajan Bose",
    "Deepak Menon", "Ashok Rao", "Vijay Joshi",
]

AMERICAN_FEMALE_NAMES = [
    "Sarah Johnson", "Emily Davis", "Jessica Martinez", "Amanda Wilson",
    "Ashley Brown", "Megan Thompson", "Lauren Garcia", "Stephanie Lee",
    "Rachel Anderson", "Brittany Taylor", "Nicole Jackson", "Amber White",
    "Heather Harris", "Christina Robinson", "Melissa Clark",
]
AMERICAN_MALE_NAMES = [
    "Alex Carter", "Michael Smith", "James Williams", "Robert Jones",
    "David Miller", "Daniel Wilson", "Christopher Moore", "Matthew Taylor",
    "Andrew Anderson", "Joshua Thomas", "Kevin Martin", "Brian Jackson",
    "Tyler Harris", "Ryan Robinson", "Nicholas Clark",
]
AMERICAN_NB_NAMES = [
    "Jordan Blake", "Taylor Morgan", "Casey Rivera", "Riley Kim",
    "Avery Chen", "Morgan Lee", "Quinn Davis", "Reese Thompson",
]

BRITISH_FEMALE_NAMES = [
    "Emma Watson", "Charlotte Hughes", "Sophie Williams", "Olivia Jones",
    "Amelia Brown", "Isabella Smith", "Grace Davies", "Hannah Taylor",
    "Evie Wilson", "Poppy Evans",
]
BRITISH_MALE_NAMES = [
    "Oliver Thompson", "Harry Davies", "George Evans", "William Harris",
    "James Roberts", "Thomas Wilson", "Jack Brown", "Samuel Taylor",
    "Ethan Jones", "Benjamin Smith",
]

GERMAN_FEMALE_NAMES = [
    "Anna Müller", "Maria Schmidt", "Julia Weber", "Laura Meyer",
    "Lena Becker", "Sophie Fischer", "Hannah Schulz", "Emma Wagner",
]
GERMAN_MALE_NAMES = [
    "Hans Müller", "Stefan Schmidt", "Klaus Weber", "Thomas Meyer",
    "Michael Becker", "Andreas Fischer", "Martin Schulz", "Christoph Wagner",
]

FRENCH_FEMALE_NAMES = [
    "Marie Dupont", "Sophie Martin", "Camille Bernard", "Amélie Petit",
    "Céline Dubois", "Lucie Moreau", "Mathilde Laurent", "Aurélie Simon",
]
FRENCH_MALE_NAMES = [
    "Jean Dupont", "Pierre Martin", "François Bernard", "Luc Petit",
    "Nicolas Dubois", "Antoine Moreau", "Julien Laurent", "Marc Simon",
]

BRAZILIAN_FEMALE_NAMES = [
    "Ana Silva", "Maria Santos", "Juliana Oliveira", "Fernanda Costa",
    "Camila Ferreira", "Larissa Lima", "Beatriz Rodrigues", "Amanda Alves",
]
BRAZILIAN_MALE_NAMES = [
    "João Silva", "Pedro Santos", "Carlos Oliveira", "Lucas Costa",
    "Rafael Ferreira", "Thiago Lima", "Mateus Rodrigues", "Bruno Alves",
]

MEXICAN_FEMALE_NAMES = [
    "Valentina García", "Sofía López", "Isabella Martínez", "Camila Hernández",
    "Daniela Díaz", "Fernanda Sánchez", "Renata Ramírez", "Lucía Flores",
]
MEXICAN_MALE_NAMES = [
    "Santiago García", "Diego López", "Sebastián Martínez", "Mateo Hernández",
    "Andrés Díaz", "Alejandro Sánchez", "Emilio Ramírez", "Miguel Flores",
]

NIGERIAN_FEMALE_NAMES = [
    "Ngozi Obi", "Fatima Mohammed", "Chioma Eze", "Aisha Yusuf",
    "Blessing Nwachukwu", "Grace Adeyemi", "Aminat Ibrahim", "Funmi Adeleke",
]
NIGERIAN_MALE_NAMES = [
    "Chukwuemeka Obi", "Mustapha Mohammed", "Emeka Eze", "Ibrahim Yusuf",
    "Oluwaseun Nwachukwu", "Adebayo Adeyemi", "Usman Ibrahim", "Femi Adeleke",
]

SOUTH_AFRICAN_FEMALE_NAMES = [
    "Nomvula Dlamini", "Zanele Khumalo", "Lindiwe Nkosi", "Thandi Mokoena",
    "Nandi Sithole", "Busisiwe Ndlovu", "Palesa Mthembu", "Siphokazi Nxumalo",
]
SOUTH_AFRICAN_MALE_NAMES = [
    "Sipho Dlamini", "Thabo Khumalo", "Lungelo Nkosi", "Bongani Mokoena",
    "Siyanda Sithole", "Mandla Ndlovu", "Thandeka Mthembu", "Nhlanhla Nxumalo",
]

AUSTRALIAN_FEMALE_NAMES = [
    "Chloe Smith", "Ruby Johnson", "Mia Williams", "Isla Brown",
    "Zoe Wilson", "Ella Jones", "Ava Davies", "Grace Taylor",
]
AUSTRALIAN_MALE_NAMES = [
    "Liam Smith", "Noah Johnson", "Oliver Williams", "Jack Brown",
    "William Wilson", "Ethan Jones", "Lucas Davies", "Lachlan Taylor",
]

SINGAPOREAN_FEMALE_NAMES = [
    "Hui Ying Tan", "Siew Bee Lim", "Xinying Lee", "Mei Fang Wong",
    "Jasmine Ng", "Crystal Koh", "Serene Chia", "Pearl Teo",
]
SINGAPOREAN_MALE_NAMES = [
    "Wei Liang Tan", "Jian Hao Lim", "Jun Wei Lee", "Kiat Seng Wong",
    "Marcus Ng", "Aaron Koh", "Ethan Chia", "Kenneth Teo",
]

SWEDISH_FEMALE_NAMES = [
    "Astrid Lindqvist", "Maja Bergström", "Elsa Johansson", "Sigrid Larsson",
    "Elin Andersson", "Frida Karlsson", "Ingrid Nilsson", "Britta Eriksson",
]
SWEDISH_MALE_NAMES = [
    "Erik Lindqvist", "Lars Bergström", "Johan Johansson", "Anders Larsson",
    "Mikael Andersson", "Björn Karlsson", "Gunnar Nilsson", "Stefan Eriksson",
]

TURKISH_FEMALE_NAMES = [
    "Ayşe Yılmaz", "Fatma Kaya", "Zeynep Demir", "Elif Çelik",
    "Hatice Şahin", "Emine Yıldız", "Büşra Öztürk", "Selin Aydın",
]
TURKISH_MALE_NAMES = [
    "Mehmet Yılmaz", "Ali Kaya", "Mustafa Demir", "Ahmet Çelik",
    "Hüseyin Şahin", "İbrahim Yıldız", "Ömer Öztürk", "Hasan Aydın",
]

POLISH_FEMALE_NAMES = [
    "Anna Kowalska", "Maria Wiśniewska", "Katarzyna Wójcik", "Małgorzata Kowalczyk",
    "Agnieszka Kamińska", "Barbara Lewandowska", "Ewa Zielińska", "Zofia Szymańska",
]
POLISH_MALE_NAMES = [
    "Piotr Kowalski", "Andrzej Wiśniewski", "Tomasz Wójcik", "Jan Kowalczyk",
    "Krzysztof Kamiński", "Stanisław Lewandowski", "Marek Zieliński", "Józef Szymański",
]

CANADIAN_FEMALE_NAMES = [
    "Sophia Tremblay", "Emma Gagnon", "Olivia Roy", "Charlotte Côté",
    "Isabelle Bouchard", "Mia Fortin", "Camille Gauthier", "Laurie Morin",
]
CANADIAN_MALE_NAMES = [
    "Liam Tremblay", "Noah Gagnon", "Oliver Roy", "Ethan Côté",
    "Lucas Bouchard", "Logan Fortin", "Benjamin Gauthier", "William Morin",
]

DUTCH_FEMALE_NAMES = [
    "Sophie de Vries", "Emma Bakker", "Julia de Boer", "Nora Visser",
    "Lotte Smit", "Fleur Meijer", "Roos Mulder", "Lisa Bos",
]
DUTCH_MALE_NAMES = [
    "Daan de Vries", "Sem Bakker", "Lars de Boer", "Finn Visser",
    "Tim Smit", "Bas Meijer", "Joris Mulder", "Ruben Bos",
]

VIETNAMESE_FEMALE_NAMES = [
    "Nguyễn Thị Lan", "Trần Thị Mai", "Lê Thị Hoa", "Phạm Thị Linh",
    "Hoàng Thị Thu", "Võ Thị Hương", "Đặng Thị Ngọc", "Bùi Thị Hằng",
]
VIETNAMESE_MALE_NAMES = [
    "Nguyễn Văn Nam", "Trần Văn Đức", "Lê Văn Hùng", "Phạm Văn Minh",
    "Hoàng Văn Tú", "Võ Văn Quang", "Đặng Văn Bình", "Bùi Văn Thắng",
]

INDONESIAN_FEMALE_NAMES = [
    "Siti Rahayu", "Dewi Kusuma", "Nur Indah", "Eka Wulandari",
    "Rini Puspita", "Dian Safitri", "Yuni Lestari", "Tina Suryani",
]
INDONESIAN_MALE_NAMES = [
    "Budi Santoso", "Adi Nugroho", "Eko Prasetyo", "Hendra Kurniawan",
    "Joko Susilo", "Dedy Suharto", "Rudi Hartono", "Agus Setiawan",
]

EGYPTIAN_FEMALE_NAMES = [
    "Fatima Hassan", "Mariam Ali", "Nour Ahmed", "Laila Mahmoud",
    "Dina Ibrahim", "Sara Khaled", "Mona Mostafa", "Rania Youssef",
]
EGYPTIAN_MALE_NAMES = [
    "Mohamed Hassan", "Ahmed Ali", "Omar Ahmed", "Khalid Mahmoud",
    "Ibrahim Hassan", "Youssef Khaled", "Mostafa Ibrahim", "Amr Youssef",
]

ARGENTINIAN_FEMALE_NAMES = [
    "Valentina Rodríguez", "Lucía Fernández", "Martina González",
    "Camila Pérez", "Florencia López", "Agustina Sánchez",
]
ARGENTINIAN_MALE_NAMES = [
    "Mateo Rodríguez", "Lucas Fernández", "Benjamín González",
    "Tomás Pérez", "Agustín López", "Santiago Sánchez",
]

THAI_FEMALE_NAMES = [
    "Siriporn Chaiyasit", "Nattaya Srisuk", "Pornthip Kamchai",
    "Waraporn Thongkham", "Sumalee Chaiyanant", "Jintana Sombat",
]
THAI_MALE_NAMES = [
    "Somchai Chaiyasit", "Wichai Srisuk", "Prasert Kamchai",
    "Wichit Thongkham", "Surapong Chaiyanant", "Somkid Sombat",
]

# ---------------------------------------------------------------------------
# Build name pools by gender / region
# ---------------------------------------------------------------------------

NAMES_BY_REGION = {
    "Korea": {
        "F": KOREAN_FEMALE_NAMES,
        "M": KOREAN_MALE_NAMES,
        "nonbinary": KOREAN_NB_NAMES,
    },
    "Japan": {
        "F": JAPANESE_FEMALE_NAMES,
        "M": JAPANESE_MALE_NAMES,
        "nonbinary": JAPANESE_FEMALE_NAMES + JAPANESE_MALE_NAMES,
    },
    "China": {
        "F": CHINESE_FEMALE_NAMES,
        "M": CHINESE_MALE_NAMES,
        "nonbinary": CHINESE_FEMALE_NAMES + CHINESE_MALE_NAMES,
    },
    "India": {
        "F": INDIAN_FEMALE_NAMES,
        "M": INDIAN_MALE_NAMES,
        "nonbinary": INDIAN_FEMALE_NAMES + INDIAN_MALE_NAMES,
    },
    "US": {
        "F": AMERICAN_FEMALE_NAMES,
        "M": AMERICAN_MALE_NAMES,
        "nonbinary": AMERICAN_NB_NAMES,
    },
    "UK": {
        "F": BRITISH_FEMALE_NAMES,
        "M": BRITISH_MALE_NAMES,
        "nonbinary": BRITISH_FEMALE_NAMES + BRITISH_MALE_NAMES,
    },
    "Germany": {
        "F": GERMAN_FEMALE_NAMES,
        "M": GERMAN_MALE_NAMES,
        "nonbinary": GERMAN_FEMALE_NAMES + GERMAN_MALE_NAMES,
    },
    "France": {
        "F": FRENCH_FEMALE_NAMES,
        "M": FRENCH_MALE_NAMES,
        "nonbinary": FRENCH_FEMALE_NAMES + FRENCH_MALE_NAMES,
    },
    "Brazil": {
        "F": BRAZILIAN_FEMALE_NAMES,
        "M": BRAZILIAN_MALE_NAMES,
        "nonbinary": BRAZILIAN_FEMALE_NAMES + BRAZILIAN_MALE_NAMES,
    },
    "Mexico": {
        "F": MEXICAN_FEMALE_NAMES,
        "M": MEXICAN_MALE_NAMES,
        "nonbinary": MEXICAN_FEMALE_NAMES + MEXICAN_MALE_NAMES,
    },
    "Nigeria": {
        "F": NIGERIAN_FEMALE_NAMES,
        "M": NIGERIAN_MALE_NAMES,
        "nonbinary": NIGERIAN_FEMALE_NAMES + NIGERIAN_MALE_NAMES,
    },
    "SouthAfrica": {
        "F": SOUTH_AFRICAN_FEMALE_NAMES,
        "M": SOUTH_AFRICAN_MALE_NAMES,
        "nonbinary": SOUTH_AFRICAN_FEMALE_NAMES + SOUTH_AFRICAN_MALE_NAMES,
    },
    "Australia": {
        "F": AUSTRALIAN_FEMALE_NAMES,
        "M": AUSTRALIAN_MALE_NAMES,
        "nonbinary": AUSTRALIAN_FEMALE_NAMES + AUSTRALIAN_MALE_NAMES,
    },
    "Singapore": {
        "F": SINGAPOREAN_FEMALE_NAMES,
        "M": SINGAPOREAN_MALE_NAMES,
        "nonbinary": SINGAPOREAN_FEMALE_NAMES + SINGAPOREAN_MALE_NAMES,
    },
    "Sweden": {
        "F": SWEDISH_FEMALE_NAMES,
        "M": SWEDISH_MALE_NAMES,
        "nonbinary": SWEDISH_FEMALE_NAMES + SWEDISH_MALE_NAMES,
    },
    "Turkey": {
        "F": TURKISH_FEMALE_NAMES,
        "M": TURKISH_MALE_NAMES,
        "nonbinary": TURKISH_FEMALE_NAMES + TURKISH_MALE_NAMES,
    },
    "Poland": {
        "F": POLISH_FEMALE_NAMES,
        "M": POLISH_MALE_NAMES,
        "nonbinary": POLISH_FEMALE_NAMES + POLISH_MALE_NAMES,
    },
    "Canada": {
        "F": CANADIAN_FEMALE_NAMES,
        "M": CANADIAN_MALE_NAMES,
        "nonbinary": AMERICAN_NB_NAMES,
    },
    "Netherlands": {
        "F": DUTCH_FEMALE_NAMES,
        "M": DUTCH_MALE_NAMES,
        "nonbinary": DUTCH_FEMALE_NAMES + DUTCH_MALE_NAMES,
    },
    "Vietnam": {
        "F": VIETNAMESE_FEMALE_NAMES,
        "M": VIETNAMESE_MALE_NAMES,
        "nonbinary": VIETNAMESE_FEMALE_NAMES + VIETNAMESE_MALE_NAMES,
    },
    "Indonesia": {
        "F": INDONESIAN_FEMALE_NAMES,
        "M": INDONESIAN_MALE_NAMES,
        "nonbinary": INDONESIAN_FEMALE_NAMES + INDONESIAN_MALE_NAMES,
    },
    "Egypt": {
        "F": EGYPTIAN_FEMALE_NAMES,
        "M": EGYPTIAN_MALE_NAMES,
        "nonbinary": EGYPTIAN_FEMALE_NAMES + EGYPTIAN_MALE_NAMES,
    },
    "Argentina": {
        "F": ARGENTINIAN_FEMALE_NAMES,
        "M": ARGENTINIAN_MALE_NAMES,
        "nonbinary": ARGENTINIAN_FEMALE_NAMES + ARGENTINIAN_MALE_NAMES,
    },
    "Thailand": {
        "F": THAI_FEMALE_NAMES,
        "M": THAI_MALE_NAMES,
        "nonbinary": THAI_FEMALE_NAMES + THAI_MALE_NAMES,
    },
}

# ---------------------------------------------------------------------------
# Region -> city examples
# ---------------------------------------------------------------------------

REGION_CITIES = {
    "Korea": ["Seoul", "Busan", "Daegu", "Incheon", "Gwangju", "Daejeon", "Rural Gangwon", "Rural Jeolla"],
    "Japan": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Sapporo", "Rural Tohoku"],
    "China": ["Beijing", "Shanghai", "Shenzhen", "Guangzhou", "Chengdu", "Rural Sichuan"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Rural Rajasthan", "Rural Bihar"],
    "US": ["San Francisco", "New York", "Chicago", "Seattle", "Austin", "Rural Midwest", "Rural Texas", "Miami", "Boston"],
    "UK": ["London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Rural Scotland"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Rural Bavaria"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Rural Provence"],
    "Brazil": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Brasília", "Rural Bahia"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Rural Oaxaca"],
    "Nigeria": ["Lagos", "Abuja", "Kano", "Ibadan", "Rural Kaduna"],
    "SouthAfrica": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Rural Limpopo"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Rural Queensland"],
    "Singapore": ["Singapore"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Rural Norrland"],
    "Turkey": ["Istanbul", "Ankara", "Izmir", "Bursa", "Rural Anatolia"],
    "Poland": ["Warsaw", "Kraków", "Wrocław", "Gdańsk", "Rural Podlaskie"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Rural Saskatchewan"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Rural Zeeland"],
    "Vietnam": ["Ho Chi Minh City", "Hanoi", "Da Nang", "Rural Mekong Delta"],
    "Indonesia": ["Jakarta", "Surabaya", "Bandung", "Medan", "Rural Java"],
    "Egypt": ["Cairo", "Alexandria", "Giza", "Rural Upper Egypt"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Rural Patagonia"],
    "Thailand": ["Bangkok", "Chiang Mai", "Phuket", "Rural Isan"],
}

REGION_CITY_TIER = {
    "Seoul": "metro", "Busan": "metro", "Daegu": "metro", "Incheon": "metro",
    "Gwangju": "small_city", "Daejeon": "small_city",
    "Rural Gangwon": "rural", "Rural Jeolla": "rural",
    "Tokyo": "metro", "Osaka": "metro", "Kyoto": "small_city", "Yokohama": "metro",
    "Sapporo": "metro", "Rural Tohoku": "rural",
    "Beijing": "metro", "Shanghai": "metro", "Shenzhen": "metro", "Guangzhou": "metro",
    "Chengdu": "metro", "Rural Sichuan": "rural",
    "Mumbai": "metro", "Delhi": "metro", "Bangalore": "metro", "Chennai": "metro",
    "Hyderabad": "metro", "Kolkata": "metro",
    "Rural Rajasthan": "rural", "Rural Bihar": "rural",
    "San Francisco": "metro", "New York": "metro", "Chicago": "metro",
    "Seattle": "metro", "Austin": "metro", "Rural Midwest": "rural",
    "Rural Texas": "rural", "Miami": "metro", "Boston": "metro",
    "London": "metro", "Manchester": "metro", "Birmingham": "metro",
    "Leeds": "small_city", "Edinburgh": "small_city", "Rural Scotland": "rural",
    "Berlin": "metro", "Munich": "metro", "Hamburg": "metro",
    "Frankfurt": "metro", "Cologne": "metro", "Rural Bavaria": "rural",
    "Paris": "metro", "Lyon": "metro", "Marseille": "metro",
    "Toulouse": "small_city", "Rural Provence": "rural",
    "São Paulo": "metro", "Rio de Janeiro": "metro", "Belo Horizonte": "metro",
    "Brasília": "metro", "Rural Bahia": "rural",
    "Mexico City": "metro", "Guadalajara": "metro", "Monterrey": "metro",
    "Puebla": "small_city", "Rural Oaxaca": "rural",
    "Lagos": "metro", "Abuja": "metro", "Kano": "small_city",
    "Ibadan": "small_city", "Rural Kaduna": "rural",
    "Johannesburg": "metro", "Cape Town": "metro", "Durban": "metro",
    "Pretoria": "metro", "Rural Limpopo": "rural",
    "Sydney": "metro", "Melbourne": "metro", "Brisbane": "metro",
    "Perth": "metro", "Rural Queensland": "rural",
    "Singapore": "metro",
    "Stockholm": "metro", "Gothenburg": "metro", "Malmö": "small_city",
    "Uppsala": "small_city", "Rural Norrland": "rural",
    "Istanbul": "metro", "Ankara": "metro", "Izmir": "metro",
    "Bursa": "small_city", "Rural Anatolia": "rural",
    "Warsaw": "metro", "Kraków": "metro", "Wrocław": "metro",
    "Gdańsk": "small_city", "Rural Podlaskie": "rural",
    "Toronto": "metro", "Vancouver": "metro", "Montreal": "metro",
    "Calgary": "metro", "Rural Saskatchewan": "rural",
    "Amsterdam": "metro", "Rotterdam": "metro", "The Hague": "metro",
    "Utrecht": "small_city", "Rural Zeeland": "rural",
    "Ho Chi Minh City": "metro", "Hanoi": "metro", "Da Nang": "small_city",
    "Rural Mekong Delta": "rural",
    "Jakarta": "metro", "Surabaya": "metro", "Bandung": "metro",
    "Medan": "small_city", "Rural Java": "rural",
    "Cairo": "metro", "Alexandria": "metro", "Giza": "metro",
    "Rural Upper Egypt": "rural",
    "Buenos Aires": "metro", "Córdoba": "metro", "Rosario": "small_city",
    "Rural Patagonia": "rural",
    "Bangkok": "metro", "Chiang Mai": "small_city", "Phuket": "small_city",
    "Rural Isan": "rural",
}

# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

ARCHETYPES = [
    {
        "name": "Power user",
        "age_bands": ["18-24", "25-34", "35-44"],
        "savviness": [4, 5],
        "devices": ["desktop", "mobile"],
        "networks": ["fast"],
        "patience": ["low"],
        "exploration": ["goal_driven", "skimmer"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive"],
        "tech_adoption": ["early_adopter"],
        "contexts": ["returning", "from_ad"],
        "time_pressures": ["rushed", "normal"],
        "goals": [
            "Sign up and reach the dashboard as fast as possible",
            "Import existing data and set up integrations",
            "Customize workspace settings and shortcuts",
            "Access advanced analytics and export a report",
            "Set up API access and explore developer tools",
        ],
        "fw": {"psych.patience": 0.9, "psych.exploration": 0.7},
        "educations": ["college", "graduate"],
        "occupations": ["software engineer", "product manager", "data scientist"],
    },
    {
        "name": "Cautious first-timer",
        "age_bands": ["25-34", "35-44", "45-54"],
        "savviness": [2, 3],
        "devices": ["mobile", "desktop"],
        "networks": ["slow_4g", "fast"],
        "patience": ["medium", "high"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream", "laggard"],
        "contexts": ["first_visit", "from_ad"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Read through all the help text before submitting a form",
            "Verify the privacy policy before creating an account",
            "Carefully compare two subscription plans",
            "Complete onboarding step-by-step without skipping anything",
            "Contact support before making a purchase decision",
        ],
        "fw": {"psych.skepticism": 0.8, "psych.reads_instructions": 0.7},
        "educations": ["highschool", "college"],
    },
    {
        "name": "Digital newcomer elderly",
        "age_bands": ["65-74", "75+"],
        "savviness": [1, 2],
        "devices": ["mobile", "tablet"],
        "networks": ["3g_throttled", "slow_4g"],
        "patience": ["low", "medium"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["laggard"],
        "contexts": ["first_visit", "referred"],
        "time_pressures": ["relaxed"],
        "goals": [
            "Send money to a family member",
            "Find contact information for customer service",
            "View recent account activity",
            "Sign up with help from a family member",
            "Check the status of an order",
        ],
        "fw": {"tech.savviness": 0.9, "psych.patience": 0.8},
        "educations": ["primary", "highschool"],
        "a11y_weights": [("large_text", 0.5), ("low_vision", 0.2)],
    },
    {
        "name": "Screen-reader user",
        "age_bands": ["18-24", "25-34", "35-44", "45-54", "55-64"],
        "savviness": [2, 3, 4],
        "devices": ["mobile", "desktop"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium", "high"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["high", "medium"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "returning"],
        "time_pressures": ["normal", "relaxed"],
        "goals": [
            "Navigate the main menu using only keyboard",
            "Complete a form and receive confirmation",
            "Find a product and read its full description",
            "Check account balance and transaction history",
            "Sign up for a service and receive welcome email",
        ],
        "fw": {"tech.a11y": 0.95, "tech.device": 0.6},
        "a11y_forced": ["screen_reader"],
    },
    {
        "name": "Motor-impaired user",
        "age_bands": ["25-34", "35-44", "45-54", "55-64", "65-74"],
        "savviness": [2, 3, 4],
        "devices": ["desktop", "mobile"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium", "high"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["medium", "high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["returning", "first_visit"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Complete a checkout using only keyboard navigation",
            "Fill out a long form without using a mouse",
            "Access account settings and update contact info",
            "Navigate to key feature using tab key only",
            "Submit a support request with minimal input",
        ],
        "fw": {"tech.a11y": 0.9, "psych.patience": 0.6},
        "a11y_forced": ["motor"],
    },
    {
        "name": "Color-blind user",
        "age_bands": ["18-24", "25-34", "35-44", "45-54"],
        "savviness": [2, 3, 4, 5],
        "devices": ["mobile", "desktop"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium", "high", "low"],
        "exploration": ["goal_driven", "methodical", "skimmer"],
        "reads_instructions": ["medium", "low"],
        "decision_speed": ["impulsive", "deliberate"],
        "tech_adoption": ["early_adopter", "mainstream"],
        "contexts": ["returning", "first_visit", "from_ad"],
        "time_pressures": ["normal", "rushed"],
        "goals": [
            "Distinguish between status indicators on a dashboard",
            "Navigate a data visualization or chart",
            "Identify which items are in stock vs. out of stock",
            "Complete a form that uses red/green validation cues",
            "Compare options that use color coding",
        ],
        "fw": {"tech.a11y": 0.85, "psych.attention_to_detail": 0.6},
        "a11y_forced": ["color_blind"],
    },
    {
        "name": "Low-vision user",
        "age_bands": ["45-54", "55-64", "65-74", "75+"],
        "savviness": [1, 2, 3],
        "devices": ["mobile", "tablet", "desktop"],
        "networks": ["slow_4g", "fast"],
        "patience": ["medium", "high"],
        "exploration": ["methodical"],
        "reads_instructions": ["high", "medium"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream", "laggard"],
        "contexts": ["returning", "first_visit"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Read product descriptions using zoom/large font",
            "Navigate to key section with magnification enabled",
            "Complete account registration without missing fields",
            "Find and read terms and conditions",
            "Check order status and view confirmation details",
        ],
        "fw": {"tech.a11y": 0.9, "tech.savviness": 0.6},
        "a11y_forced": ["low_vision"],
    },
    {
        "name": "Mobile on slow network",
        "age_bands": ["13-17", "18-24", "25-34", "35-44", "45-54"],
        "savviness": [1, 2, 3],
        "devices": ["mobile"],
        "networks": ["3g_throttled"],
        "patience": ["low", "medium"],
        "exploration": ["skimmer", "goal_driven"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive", "deliberate"],
        "tech_adoption": ["mainstream", "laggard"],
        "contexts": ["from_ad", "first_visit", "returning"],
        "time_pressures": ["normal", "rushed"],
        "goals": [
            "Load the home page and find a product quickly",
            "Complete a mobile checkout before network drops",
            "Browse a catalog with images on slow connection",
            "Sign in and reach the dashboard quickly",
            "Find opening hours or contact info without loading heavy content",
        ],
        "fw": {"tech.network": 0.9, "tech.device": 0.7},
        "educations": ["primary", "highschool", "college"],
    },
    {
        "name": "Price-sensitive shopper",
        "age_bands": ["18-24", "25-34", "35-44", "45-54"],
        "savviness": [2, 3, 4],
        "devices": ["mobile", "desktop"],
        "networks": ["slow_4g", "fast"],
        "patience": ["high", "medium"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["medium", "high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "returning", "from_ad"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Compare prices across multiple products before buying",
            "Find coupon codes and apply them at checkout",
            "Compare subscription tiers and select the cheapest viable plan",
            "Calculate total cost including shipping and tax",
            "Wait for a sale before completing a purchase",
        ],
        "fw": {"attitudes.price_sensitivity": 0.9, "psych.decision_speed": 0.7},
        "price_sensitivity": "high",
    },
    {
        "name": "Privacy-focused user",
        "age_bands": ["25-34", "35-44", "45-54", "55-64"],
        "savviness": [3, 4, 5],
        "devices": ["desktop", "mobile"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium", "high"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["early_adopter", "mainstream"],
        "contexts": ["first_visit", "from_ad"],
        "time_pressures": ["normal", "relaxed"],
        "goals": [
            "Audit cookie and data-sharing settings before signing up",
            "Request a data export and review personal data stored",
            "Delete account and verify all data is removed",
            "Configure privacy settings to the most restrictive option",
            "Sign up without providing optional personal information",
        ],
        "fw": {"attitudes.privacy_sensitivity": 0.95, "psych.reads_instructions": 0.7},
        "privacy_sensitivity": "high",
    },
    {
        "name": "Impulse buyer",
        "age_bands": ["18-24", "25-34", "35-44"],
        "savviness": [3, 4],
        "devices": ["mobile"],
        "networks": ["fast", "slow_4g"],
        "patience": ["low"],
        "exploration": ["skimmer"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive"],
        "tech_adoption": ["early_adopter", "mainstream"],
        "contexts": ["from_ad", "referred"],
        "time_pressures": ["rushed", "normal"],
        "goals": [
            "Buy a product immediately after seeing a social media ad",
            "One-tap checkout from a product page",
            "Add to cart and pay in under two minutes",
            "Redeem a limited-time offer before it expires",
            "Complete a flash sale purchase on mobile",
        ],
        "fw": {"psych.decision_speed": 0.9, "psych.patience": 0.8},
    },
    {
        "name": "Student",
        "age_bands": ["13-17", "18-24", "25-34"],
        "savviness": [3, 4],
        "devices": ["mobile", "desktop", "tablet"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium"],
        "exploration": ["skimmer", "goal_driven"],
        "reads_instructions": ["low", "medium"],
        "decision_speed": ["deliberate", "impulsive"],
        "tech_adoption": ["early_adopter", "mainstream"],
        "contexts": ["first_visit", "referred", "from_ad"],
        "time_pressures": ["normal", "rushed"],
        "goals": [
            "Find free or student-discounted resources",
            "Sign up with a student email for a discount",
            "Submit an assignment or upload a document",
            "Search for information to complete coursework",
            "Set up a free account and explore core features",
        ],
        "fw": {"attitudes.price_sensitivity": 0.7, "psych.exploration": 0.6},
        "price_sensitivity": "high",
        "educations": ["highschool", "college"],
    },
    {
        "name": "Professional",
        "age_bands": ["25-34", "35-44", "45-54"],
        "savviness": [3, 4, 5],
        "devices": ["desktop", "mobile"],
        "networks": ["fast"],
        "patience": ["medium", "low"],
        "exploration": ["goal_driven"],
        "reads_instructions": ["low", "medium"],
        "decision_speed": ["deliberate", "impulsive"],
        "tech_adoption": ["early_adopter", "mainstream"],
        "contexts": ["returning", "first_visit"],
        "time_pressures": ["rushed", "normal"],
        "goals": [
            "Complete a task quickly between meetings",
            "Generate a report and share it with a team",
            "Integrate a tool with an existing workflow",
            "Onboard and be productive within 10 minutes",
            "Access key metrics from the dashboard",
        ],
        "fw": {"psych.patience": 0.7, "psych.exploration": 0.6},
        "educations": ["college", "graduate"],
        "occupations": ["consultant", "lawyer", "marketing manager", "financial analyst", "HR professional"],
    },
    {
        "name": "Enterprise decision-maker",
        "age_bands": ["35-44", "45-54", "55-64"],
        "savviness": [3, 4],
        "devices": ["desktop"],
        "networks": ["fast"],
        "patience": ["high", "medium"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["medium", "high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "from_ad"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Evaluate enterprise pricing and request a demo",
            "Review security and compliance documentation",
            "Compare two enterprise vendors on capabilities",
            "Request a trial and test for team fit",
            "Understand the onboarding process for a 50-person team",
        ],
        "fw": {"attitudes.price_sensitivity": 0.5, "psych.reads_instructions": 0.8},
        "educations": ["graduate", "college"],
        "occupations": ["CTO", "VP of Engineering", "Director of Operations", "Head of IT", "Chief Information Officer"],
    },
    {
        "name": "Small business owner",
        "age_bands": ["25-34", "35-44", "45-54"],
        "savviness": [2, 3, 4],
        "devices": ["mobile", "desktop"],
        "networks": ["fast", "slow_4g"],
        "patience": ["medium"],
        "exploration": ["goal_driven", "methodical"],
        "reads_instructions": ["medium"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "from_ad", "referred"],
        "time_pressures": ["normal", "rushed"],
        "goals": [
            "Set up a business account and invite team members",
            "Process a customer payment or invoice",
            "Track inventory or manage product listings",
            "Review monthly performance and revenue reports",
            "Connect payment gateway and test checkout flow",
        ],
        "fw": {"psych.exploration": 0.6, "attitudes.price_sensitivity": 0.7},
        "price_sensitivity": "medium",
        "occupations": ["cafe owner", "retail shop owner", "freelancer", "hair salon owner", "food truck operator"],
    },
    {
        "name": "Digital nomad",
        "age_bands": ["18-24", "25-34", "35-44"],
        "savviness": [4, 5],
        "devices": ["laptop/desktop", "mobile"],
        "networks": ["slow_4g", "fast"],
        "patience": ["medium", "low"],
        "exploration": ["goal_driven", "skimmer"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive", "deliberate"],
        "tech_adoption": ["early_adopter"],
        "contexts": ["returning", "first_visit"],
        "time_pressures": ["normal", "rushed"],
        "goals": [
            "Sign in from a new country without triggering security blocks",
            "Update billing address to a new country",
            "Access files and collaborate remotely from a café",
            "Switch between multiple accounts for different clients",
            "Set up VPN-compatible workflow on a new device",
        ],
        "fw": {"tech.savviness": 0.7, "tech.network": 0.7},
        "educations": ["college", "graduate"],
    },
    {
        "name": "Gen Z social media native",
        "age_bands": ["13-17", "18-24"],
        "savviness": [3, 4, 5],
        "devices": ["mobile"],
        "networks": ["fast", "slow_4g"],
        "patience": ["low"],
        "exploration": ["skimmer"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive"],
        "tech_adoption": ["early_adopter"],
        "contexts": ["from_ad", "referred"],
        "time_pressures": ["rushed", "normal"],
        "goals": [
            "Share content or a result directly to social media",
            "Sign up with an existing social login in one tap",
            "Browse a product catalog inspired by a TikTok video",
            "Find trending content and interact with it",
            "Complete a quick quiz or interactive feature",
        ],
        "fw": {"psych.patience": 0.9, "psych.decision_speed": 0.8},
        "price_sensitivity": "high",
    },
    {
        "name": "Retired professional",
        "age_bands": ["55-64", "65-74", "75+"],
        "savviness": [2, 3],
        "devices": ["desktop", "tablet"],
        "networks": ["fast", "slow_4g"],
        "patience": ["high", "medium"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream", "laggard"],
        "contexts": ["first_visit", "referred"],
        "time_pressures": ["relaxed"],
        "goals": [
            "Learn a new digital tool with step-by-step guidance",
            "Manage finances or retirement accounts online",
            "Set up video call access for family communication",
            "Find and subscribe to health-related information",
            "Review account history and download statements",
        ],
        "fw": {"tech.savviness": 0.7, "psych.reads_instructions": 0.7},
        "educations": ["college", "graduate"],
        "a11y_weights": [("large_text", 0.4), ("low_vision", 0.15)],
        "occupations": ["retired teacher", "retired engineer", "retired executive"],
    },
    {
        "name": "Caregiver/parent",
        "age_bands": ["25-34", "35-44", "45-54"],
        "savviness": [2, 3, 4],
        "devices": ["mobile", "tablet"],
        "networks": ["fast", "slow_4g"],
        "patience": ["low", "medium"],
        "exploration": ["goal_driven"],
        "reads_instructions": ["low", "medium"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "returning", "referred"],
        "time_pressures": ["rushed", "normal"],
        "goals": [
            "Find and book a children's service or appointment",
            "Manage household subscriptions in one place",
            "Set up parental controls or family sharing",
            "Pay a bill or manage a family account quickly",
            "Track a delivery while managing kids",
        ],
        "fw": {"psych.patience": 0.8, "psych.time_pressure": 0.7},
        "household": "family_with_kids",
    },
    {
        "name": "Rural user",
        "age_bands": ["25-34", "35-44", "45-54", "55-64", "65-74"],
        "savviness": [1, 2, 3],
        "devices": ["mobile"],
        "networks": ["3g_throttled"],
        "patience": ["medium", "high"],
        "exploration": ["methodical", "goal_driven"],
        "reads_instructions": ["medium", "high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["laggard", "mainstream"],
        "contexts": ["first_visit", "referred"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Access government or agricultural services online",
            "Find nearby service providers using location",
            "Submit a form or application on mobile",
            "Purchase goods and have them delivered to a rural address",
            "Connect with family or community groups online",
        ],
        "fw": {"tech.network": 0.9, "tech.savviness": 0.7},
    },
    {
        "name": "Urban commuter",
        "age_bands": ["18-24", "25-34", "35-44"],
        "savviness": [3, 4],
        "devices": ["mobile"],
        "networks": ["slow_4g", "fast"],
        "patience": ["low"],
        "exploration": ["skimmer", "goal_driven"],
        "reads_instructions": ["low"],
        "decision_speed": ["impulsive"],
        "tech_adoption": ["mainstream", "early_adopter"],
        "contexts": ["returning", "from_ad"],
        "time_pressures": ["rushed"],
        "goals": [
            "Complete a task during a 10-minute subway ride",
            "Check account status while commuting",
            "Make a quick purchase before a stop",
            "Book a service for later in the day",
            "Read key information with one hand on mobile",
        ],
        "fw": {"psych.patience": 0.9, "tech.device": 0.7},
    },
    {
        "name": "Non-native speaker",
        "age_bands": ["18-24", "25-34", "35-44", "45-54"],
        "savviness": [2, 3, 4],
        "devices": ["mobile", "desktop"],
        "networks": ["slow_4g", "fast"],
        "patience": ["medium", "high"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream"],
        "contexts": ["first_visit", "from_ad"],
        "time_pressures": ["normal", "relaxed"],
        "goals": [
            "Navigate an interface not in the user's native language",
            "Find a language switcher and change the interface language",
            "Complete a form with unfamiliar terminology",
            "Understand error messages written in a foreign language",
            "Use translation tools alongside the app to complete onboarding",
        ],
        "fw": {"demographics.primary_language": 0.8, "psych.reads_instructions": 0.7},
    },
    {
        "name": "Cognitive accessibility user",
        "age_bands": ["18-24", "25-34", "35-44", "45-54"],
        "savviness": [1, 2, 3],
        "devices": ["mobile", "tablet"],
        "networks": ["slow_4g", "fast"],
        "patience": ["medium", "high"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream", "laggard"],
        "contexts": ["first_visit", "returning"],
        "time_pressures": ["relaxed"],
        "goals": [
            "Follow a step-by-step wizard without getting lost",
            "Complete a form with clear labels and no distractions",
            "Find help content written in plain language",
            "Navigate with consistent layout and predictable interactions",
            "Complete a multi-step task with progress indicators",
        ],
        "fw": {"tech.savviness": 0.8, "psych.exploration": 0.7},
    },
    {
        "name": "Tech laggard",
        "age_bands": ["45-54", "55-64", "65-74", "75+"],
        "savviness": [1, 2],
        "devices": ["desktop", "mobile"],
        "networks": ["slow_4g", "3g_throttled", "fast"],
        "patience": ["low", "medium"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["laggard"],
        "contexts": ["first_visit", "referred"],
        "time_pressures": ["relaxed"],
        "goals": [
            "Complete a basic task without prior training",
            "Find the login button and sign in",
            "Recover a forgotten password via email",
            "Contact support by phone or chat",
            "Find a physical address or store location",
        ],
        "fw": {"tech.savviness": 0.95, "tech.adoption": 0.8},
        "educations": ["primary", "highschool"],
    },
    {
        "name": "Research-oriented academic",
        "age_bands": ["18-24", "25-34", "35-44"],
        "savviness": [4, 5],
        "devices": ["desktop"],
        "networks": ["fast"],
        "patience": ["high"],
        "exploration": ["methodical"],
        "reads_instructions": ["high"],
        "decision_speed": ["deliberate"],
        "tech_adoption": ["mainstream", "early_adopter"],
        "contexts": ["first_visit", "returning"],
        "time_pressures": ["relaxed", "normal"],
        "goals": [
            "Search and filter a large dataset or catalog",
            "Export data in a structured format for analysis",
            "Cite or reference content from the platform",
            "Find advanced search filters and apply them",
            "Compare multiple items side-by-side in detail",
        ],
        "fw": {"psych.attention_to_detail": 0.9, "psych.reads_instructions": 0.8},
        "educations": ["graduate"],
        "occupations": ["PhD student", "researcher", "university lecturer", "postdoc"],
    },
]

# ---------------------------------------------------------------------------
# Distribution: how many personas per archetype (proportional, sums to 500)
# ---------------------------------------------------------------------------

# 25 archetypes; we'll assign a base count and top up to exactly 500
BASE_PER_ARCHETYPE = 500 // len(ARCHETYPES)  # = 20
REMAINDER = 500 - BASE_PER_ARCHETYPE * len(ARCHETYPES)  # = 0

ARCHETYPE_COUNTS = {}
for i, arch in enumerate(ARCHETYPES):
    ARCHETYPE_COUNTS[arch["name"]] = BASE_PER_ARCHETYPE + (1 if i < REMAINDER else 0)

# ---------------------------------------------------------------------------
# Region distribution (spread evenly over 500 personas, cycling)
# ---------------------------------------------------------------------------

REGIONS = list(REGION_CITIES.keys())

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def pick(lst, weights=None):
    if weights:
        return random.choices(lst, weights=weights, k=1)[0]
    return random.choice(lst)


def pick_name(gender: str, region_key: str, used: set) -> str:
    pool = NAMES_BY_REGION.get(region_key, {}).get(gender, [])
    if not pool:
        # fallback: all names for that region
        all_names = []
        for v in NAMES_BY_REGION.get(region_key, {}).values():
            all_names.extend(v)
        if not all_names:
            # absolute fallback
            return f"User_{len(used)+1}"
        pool = all_names
    # Try to pick unused; if exhausted add a numeric suffix
    candidates = [n for n in pool if n not in used]
    if not candidates:
        base = random.choice(pool)
        suffix = len(used)
        return f"{base} {suffix}"
    name = random.choice(candidates)
    used.add(name)
    return name


def _yaml_str(value) -> str:
    """Return a YAML-safe quoted string."""
    s = str(value)
    # Quote if contains special chars or is ambiguous
    needs_quote = any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'", '\n'))
    if needs_quote:
        return f'"{s}"'
    return s


def education_for_age(age_band: str, allowed: list | None) -> str:
    if allowed:
        pool = allowed
    else:
        pool = EDUCATIONS
    # Restrict by age
    if age_band == "13-17":
        pool = [e for e in pool if e in ("primary", "highschool", "none")]
        if not pool:
            pool = ["highschool"]
    elif age_band == "18-24":
        pool = [e for e in pool if e in ("highschool", "college", "graduate", "none")]
        if not pool:
            pool = ["highschool", "college"]
    return random.choice(pool) if pool else "highschool"


def savviness_for_age(age_band: str, archetype_savviness: list) -> int:
    sav = random.choice(archetype_savviness)
    if age_band in ("65-74", "75+") and sav > 3:
        sav = 3
    if age_band == "13-17" and sav > 4:
        sav = 4
    return sav


def a11y_for_persona(archetype: dict, age_band: str, savviness: int) -> list:
    if "a11y_forced" in archetype:
        extras = archetype.get("a11y_weights", [])
        result = list(archetype["a11y_forced"])
        for need, prob in extras:
            if need not in result and random.random() < prob:
                result.append(need)
        return result

    result = []
    weights = archetype.get("a11y_weights", [])
    for need, prob in weights:
        if random.random() < prob:
            result.append(need)

    # Age-based probability
    if age_band in ("65-74", "75+") and not result:
        roll = random.random()
        if roll < 0.3:
            result.append("large_text")
        elif roll < 0.45:
            result.append("low_vision")

    return result


def build_os(device: str, savviness: int) -> str:
    # For desktop, high savviness -> higher linux probability
    if device == "desktop" and savviness >= 4:
        return pick(["windows", "macos", "linux"], [0.45, 0.35, 0.20])
    if device == "laptop/desktop":
        device = "desktop"
    os_list, os_weights = OS_BY_DEVICE.get(device, (["windows"], [1.0]))
    return pick(os_list, os_weights)


def build_network(archetype: dict, device: str, city: str) -> str:
    # Rural cities get worse network
    tier = REGION_CITY_TIER.get(city, "metro")
    if tier == "rural":
        return pick(["slow_4g", "3g_throttled"], [0.4, 0.6])
    return pick(archetype["networks"])


def build_factor_weights(archetype: dict, extra: dict | None = None) -> dict:
    fw = dict(archetype["fw"])
    if extra:
        fw.update(extra)
    return fw


# ---------------------------------------------------------------------------
# Inline YAML writer (avoids needing PyYAML installed, gives exact formatting)
# ---------------------------------------------------------------------------

def quote_yaml(value: str) -> str:
    if '"' in value:
        value = value.replace('"', '\\"')
    return f'"{value}"'


def write_a11y(needs: list) -> str:
    if not needs:
        return "[]"
    inner = ", ".join(quote_yaml(n) for n in needs)
    return f"[{inner}]"


def write_factor_weights(fw: dict) -> str:
    parts = []
    for k, v in fw.items():
        parts.append(f'{quote_yaml(k)}: {v}')
    return "{ " + ", ".join(parts) + " }"


def persona_to_yaml(p: dict) -> str:
    lines = []
    lines.append(f'- name: {quote_yaml(p["name"])}')
    lines.append(f'  archetype: {quote_yaml(p["archetype"])}')

    # demographics
    d = p["demographics"]
    parts = []
    parts.append(f'age_band: {quote_yaml(d["age_band"])}')
    parts.append(f'gender: {d["gender"]}')
    parts.append(f'region: {quote_yaml(d["region"])}')
    parts.append(f'city_tier: {d["city_tier"]}')
    if "primary_language" in d:
        parts.append(f'primary_language: {quote_yaml(d["primary_language"])}')
    parts.append(f'education: {d["education"]}')
    if "occupation" in d:
        parts.append(f'occupation: {quote_yaml(d["occupation"])}')
    if "household" in d:
        parts.append(f'household: {d["household"]}')
    lines.append(f'  demographics: {{ {", ".join(parts)} }}')

    # tech
    t = p["tech"]
    tparts = []
    tparts.append(f'savviness: {t["savviness"]}')
    device = t["device"]
    if device == "laptop/desktop":
        device = "desktop"
    tparts.append(f'device: {device}')
    tparts.append(f'os: {t["os"]}')
    tparts.append(f'network: {quote_yaml(t["network"])}')
    if t.get("a11y"):
        tparts.append(f'a11y: {write_a11y(t["a11y"])}')
    lines.append(f'  tech: {{ {", ".join(tparts)} }}')

    # psych
    ps = p["psych"]
    psparts = []
    psparts.append(f'patience: {ps["patience"]}')
    psparts.append(f'exploration: {ps["exploration"]}')
    if "reads_instructions" in ps:
        psparts.append(f'reads_instructions: {ps["reads_instructions"]}')
    if "decision_speed" in ps:
        psparts.append(f'decision_speed: {ps["decision_speed"]}')
    if "skepticism" in ps:
        psparts.append(f'skepticism: {ps["skepticism"]}')
    lines.append(f'  psych: {{ {", ".join(psparts)} }}')

    # attitudes (only if non-empty)
    att = p.get("attitudes", {})
    attparts = []
    if "privacy_sensitivity" in att:
        attparts.append(f'privacy_sensitivity: {att["privacy_sensitivity"]}')
    if "price_sensitivity" in att:
        attparts.append(f'price_sensitivity: {att["price_sensitivity"]}')
    if "tech_adoption" in att:
        attparts.append(f'tech_adoption: {att["tech_adoption"]}')
    if attparts:
        lines.append(f'  attitudes: {{ {", ".join(attparts)} }}')

    # intent
    i = p["intent"]
    iparts = []
    iparts.append(f'goal: {quote_yaml(i["goal"])}')
    iparts.append(f'context: {i["context"]}')
    iparts.append(f'time_pressure: {i["time_pressure"]}')
    lines.append(f'  intent: {{ {", ".join(iparts)} }}')

    # factor_weights
    lines.append(f'  factor_weights: {write_factor_weights(p["factor_weights"])}')
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_personas(n: int = 500) -> list[dict]:
    personas = []
    used_names: set[str] = set()

    # Pre-build a cycling region list so regions are spread evenly
    region_cycle = []
    while len(region_cycle) < n:
        region_cycle.extend(REGIONS)
    random.shuffle(region_cycle)
    region_iter = iter(region_cycle)

    # Build persona counts per archetype
    counts = list(ARCHETYPE_COUNTS.items())
    random.shuffle(counts)

    for arch_name, count in counts:
        arch = next(a for a in ARCHETYPES if a["name"] == arch_name)
        for _ in range(count):
            # Region
            region_key = next(region_iter)

            # City within region
            city = pick(REGION_CITIES[region_key])
            city_tier = REGION_CITY_TIER.get(city, "metro")

            # Gender
            gender = pick(GENDERS, GENDER_WEIGHTS)

            # Name
            name = pick_name(gender, region_key, used_names)

            # Age band
            age_band = pick(arch["age_bands"])

            # Savviness
            savviness = savviness_for_age(age_band, arch["savviness"])

            # Device — guard "laptop/desktop"
            device_raw = pick(arch["devices"])
            device = "desktop" if device_raw == "laptop/desktop" else device_raw

            # OS
            os_ = build_os(device_raw, savviness)

            # Network
            network = build_network(arch, device, city)

            # Education
            edu = education_for_age(age_band, arch.get("educations"))

            # A11y
            a11y = a11y_for_persona(arch, age_band, savviness)

            # Psych
            patience = pick(arch["patience"])
            exploration = pick(arch["exploration"])
            reads_instructions = pick(arch["reads_instructions"])
            decision_speed = pick(arch.get("decision_speed", ["deliberate"]))

            psych = {
                "patience": patience,
                "exploration": exploration,
                "reads_instructions": reads_instructions,
                "decision_speed": decision_speed,
            }

            # Skepticism for cautious types
            if arch_name in ("Cautious first-timer", "Privacy-focused user"):
                psych["skepticism"] = "high"
            elif arch_name in ("Power user", "Gen Z social media native"):
                psych["skepticism"] = "low"

            # Attitudes
            attitudes = {}
            tech_adoption = pick(arch.get("tech_adoption", ["mainstream"]))
            attitudes["tech_adoption"] = tech_adoption

            if "privacy_sensitivity" in arch:
                attitudes["privacy_sensitivity"] = arch["privacy_sensitivity"]
            elif arch_name in ("Privacy-focused user",):
                attitudes["privacy_sensitivity"] = "high"
            else:
                attitudes["privacy_sensitivity"] = pick(["low", "medium", "high"], [0.3, 0.4, 0.3])

            if "price_sensitivity" in arch:
                attitudes["price_sensitivity"] = arch["price_sensitivity"]
            else:
                attitudes["price_sensitivity"] = pick(["low", "medium", "high"], [0.25, 0.45, 0.30])

            # Goal
            goal = pick(arch["goals"])

            # Context & time pressure
            context = pick(arch["contexts"])
            time_pressure = pick(arch["time_pressures"])

            # Factor weights
            fw = build_factor_weights(arch)

            # Optional fields
            demo_extra = {}
            if "occupations" in arch:
                demo_extra["occupation"] = pick(arch["occupations"])
            if "household" in arch:
                demo_extra["household"] = arch["household"]

            # Non-native speaker: add primary_language hint
            if arch_name == "Non-native speaker":
                lang_map = {
                    "Korea": "Korean",
                    "Japan": "Japanese",
                    "China": "Mandarin",
                    "India": "Hindi",
                    "Brazil": "Portuguese",
                    "Mexico": "Spanish",
                    "France": "French",
                    "Germany": "German",
                    "Vietnam": "Vietnamese",
                    "Indonesia": "Indonesian",
                    "Egypt": "Arabic",
                    "Turkey": "Turkish",
                    "Poland": "Polish",
                    "Thailand": "Thai",
                    "Nigeria": "Yoruba",
                    "SouthAfrica": "Zulu",
                    "Argentina": "Spanish",
                    "Netherlands": "Dutch",
                }
                lang = lang_map.get(region_key, "English")
                demo_extra["primary_language"] = lang

            persona = {
                "name": name,
                "archetype": arch["name"],
                "demographics": {
                    "age_band": age_band,
                    "gender": gender,
                    "region": city,
                    "city_tier": city_tier,
                    "education": edu,
                    **demo_extra,
                },
                "tech": {
                    "savviness": savviness,
                    "device": device,
                    "os": os_,
                    "network": network,
                    **({"a11y": a11y} if a11y else {}),
                },
                "psych": psych,
                "attitudes": attitudes,
                "intent": {
                    "goal": goal,
                    "context": context,
                    "time_pressure": time_pressure,
                },
                "factor_weights": fw,
            }
            personas.append(persona)

    # Shuffle the final list so archetypes are interleaved
    random.shuffle(personas)
    return personas[:n]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    personas = generate_personas(500)
    assert len(personas) == 500, f"Expected 500, got {len(personas)}"

    header = textwrap.dedent("""\
        # Reusable archetype personas for the SynthPanel library.
        # 500 diverse personas spanning archetypes, demographics, tech profiles, and goals.
        """)

    body_lines = []
    for p in personas:
        body_lines.append(persona_to_yaml(p))

    content = header + "\n" + "\n".join(body_lines)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"Written {len(personas)} personas to {OUT}")

    # Verification
    import re
    found = len(re.findall(r'^- name:', content, re.MULTILINE))
    print(f"Verification: {found} '- name:' entries found in file")
    assert found == 500, f"Count mismatch! {found}"
    print("All checks passed.")


if __name__ == "__main__":
    main()
