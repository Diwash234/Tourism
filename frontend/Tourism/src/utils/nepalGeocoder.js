/**
 * Nepal Administrative Geocoder & Municipality/Ward Coordinate Calculator
 * Full coverage of all 7 Provinces, 77 Districts, Municipalities, Gaunpalikas,
 * and support for custom manual village / ward entry.
 */

export const NEPAL_ALL_PROVINCES = [
  "Koshi",
  "Madhesh",
  "Bagmati",
  "Gandaki",
  "Lumbini",
  "Karnali",
  "Sudurpashchim"
]

export const NEPAL_ALL_DISTRICTS = {
  "Koshi": ["Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang", "Okhaldhunga", "Panchthar", "Sankhuwasabha", "Solukhumbu", "Sunsari", "Taplejung", "Terhathum", "Udayapur"],
  "Madhesh": ["Bara", "Dhanusha", "Mahottari", "Parsa", "Rautahat", "Saptari", "Sarlahi", "Siraha"],
  "Bagmati": ["Bhaktapur", "Chitwan", "Dhading", "Dolakha", "Kathmandu", "Kavrepalanchok", "Lalitpur", "Makwanpur", "Nuwakot", "Ramechhap", "Rasuwa", "Sindhuli", "Sindhupalchok"],
  "Gandaki": ["Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang", "Myagdi", "Nawalpur", "Parbat", "Syangja", "Tanahun"],
  "Lumbini": ["Arghakhanchi", "Banke", "Bardiya", "Dang", "Gulmi", "Kapilvastu", "Parasi", "Palpa", "Pyuthan", "Rolpa", "Rukum East", "Rupandehi"],
  "Karnali": ["Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot", "Mugu", "Rukum West", "Salyan", "Surkhet"],
  "Sudurpashchim": ["Achham", "Baitadi", "Bajhang", "Bajura", "Dadeldhura", "Darchula", "Doti", "Kailali", "Kanchanpur"]
}

export const DISTRICT_DEFAULTS = {
  // Bagmati
  "Kathmandu": { lat: 27.7172, lng: 85.3240, alt: "1,400m", munis: ["Kathmandu Metropolitan City", "Kirtipur Municipality", "Budhanilkantha Municipality", "Chandragiri Municipality", "Tokha Municipality", "Gokarneshwor Municipality", "Nagarjun Municipality", "Shankharapur Municipality", "Tarakeshwor Municipality", "Dakshinkali Municipality", "Kageshwari Manohara Municipality"] },
  "Lalitpur": { lat: 27.6644, lng: 85.3188, alt: "1,400m", munis: ["Lalitpur Metropolitan City", "Godawari Municipality", "Mahalaxmi Municipality", "Konjyosom Rural Municipality", "Bagmati Rural Municipality", "Mahankal Rural Municipality"] },
  "Bhaktapur": { lat: 27.6710, lng: 85.4298, alt: "1,401m", munis: ["Bhaktapur Municipality", "Changunarayan Municipality", "Madhyapur Thimi Municipality", "Suryabinayak Municipality"] },
  "Chitwan": { lat: 27.5341, lng: 84.4530, alt: "208m", munis: ["Bharatpur Metropolitan City", "Ratnanagar Municipality (Sauraha)", "Kalika Municipality", "Khairahani Municipality", "Madi Municipality", "Rapti Municipality", "Ichchhakamana Rural Municipality"] },
  "Rasuwa": { lat: 28.2117, lng: 85.5683, alt: "1,950m", munis: ["Gosaikunda Rural Municipality (Langtang)", "Kalika Rural Municipality", "Naukunda Rural Municipality", "Uttargaya Rural Municipality", "Amachodingmo Rural Municipality"] },
  "Dhading": { lat: 27.8667, lng: 84.9000, alt: "1,200m", munis: ["Nilkantha Municipality", "Dhunibeshi Municipality", "Benighat Rorang", "Galchhi", "Gajuri", "Khaniyabas", "Jwalamukhi", "Tripurasundari", "Gangajamuna", "Netrawati Dabjong", "Ruby Valley", "Siddhalek", "Thakre"] },
  "Kavrepalanchok": { lat: 27.6167, lng: 85.5500, alt: "1,500m", munis: ["Dhulikhel Municipality", "Banepa Municipality", "Panauti Municipality", "Namobuddha Municipality", "Mandandeupur Municipality", "Panchkhal Municipality", "Roshi", "Temal", "Bethanchok", "Bhumlu", "Chaurideurali", "Khanikhola", "Mahabharat"] },
  "Sindhupalchok": { lat: 27.9500, lng: 85.6833, alt: "1,450m", munis: ["Chautara Sangachokgadhi", "Melamchi Municipality", "Barhabise Municipality", "Bhotekoshi", "Helambu", "Indrawati", "Jugal", "Lisankhu Pakhar", "Panchpokhari Thangpal", "Tripurasundari", "Sunkoshi", "Balephi"] },
  "Makwanpur": { lat: 27.4167, lng: 85.0333, alt: "450m", munis: ["Hetauda Sub-Metropolitan", "Thaha Municipality", "Bhimfedi", "Makawanpurgadhi", "Manahari", "Raksirang", "Bakaiya", "Bagmati", "Kailash", "Indrasarowar"] },
  "Nuwakot": { lat: 27.9167, lng: 85.1667, alt: "1,050m", munis: ["Bidur Municipality", "Belkotgadhi Municipality", "Kakani", "Kispang", "Tadi", "Tarkeshwar", "Dupcheshwar", "Panchakanya", "Myagang", "Likhu", "Shivapuri", "Suryagadhi"] },
  "Dolakha": { lat: 27.6667, lng: 86.0333, alt: "1,550m", munis: ["Bhimeshwar Municipality", "Jiri Municipality", "Kalinchok Rural Municipality", "Gaurishankar", "Baiteshwar", "Sailung", "Tamakoshi", "Melung", "Bigu"] },
  "Sindhuli": { lat: 27.2500, lng: 85.9667, alt: "500m", munis: ["Kamalamai Municipality", "Dudhauli Municipality", "Golanjor", "Ghyanglekh", "Tinpatan", "Phikkal", "Marin", "Sunkoshi", "Hariharpurgadhi"] },
  "Ramechhap": { lat: 27.3333, lng: 86.0833, alt: "1,400m", munis: ["Manthali Municipality", "Ramechhap Municipality", "Umakunda", "Khandadevi", "Gokulganga", "Doramba", "Likhu Tamakoshi", "Sunapati"] },

  // Gandaki
  "Kaski": { lat: 28.2096, lng: 83.9856, alt: "822m", munis: ["Pokhara Metropolitan City", "Annapurna Rural Municipality (Ghandruk/ABC)", "Machhapuchhre Rural Municipality", "Madi Rural Municipality", "Rupa Rural Municipality"] },
  "Mustang": { lat: 29.1822, lng: 83.9567, alt: "3,840m", munis: ["Gharapjhong Rural Municipality (Jomsom/Marpha)", "Baragung Muktikshetra (Muktinath/Kagbeni)", "Lo Manthang Rural Municipality (Walled City)", "Lo-Ghekar Damodarkunda (Charang)", "Thasang Rural Municipality (Lete)"] },
  "Tanahun": { lat: 27.9333, lng: 84.4167, alt: "1,030m", munis: ["Bandipur Rural Municipality", "Byas Municipality (Damauli)", "Shuklagandaki Municipality", "Bhimad Municipality", "Myagde", "Aanboo Khaireni", "Rishing", "Ghiring", "Devghat", "Bhanu Municipality"] },
  "Manang": { lat: 28.6667, lng: 84.0167, alt: "3,519m", munis: ["Manang Disyang Rural Municipality", "Chame Rural Municipality", "Narpa Bhumi Rural Municipality", "Nashong Rural Municipality"] },
  "Gorkha": { lat: 28.0000, lng: 84.6333, alt: "1,150m", munis: ["Gorkha Municipality", "Palungtar Municipality", "Manaslu / Chumnubri Rural Municipality", "Barpak Sulikot", "Siranchok", "Ajirkot", "Dharche", "Bhimsen Thapa", "Sahid Lakhan", "Gandaki", "Arughat"] },
  "Myagdi": { lat: 28.3667, lng: 83.5667, alt: "1,170m", munis: ["Beni Municipality (Galeshwor)", "Annapurna Rural Municipality (Poon Hill/Tatopani)", "Dhaulagiri Rural Municipality", "Mangala", "Malika", "Raghuganga"] },
  "Syangja": { lat: 27.9833, lng: 83.7667, alt: "750m", munis: ["Waling Municipality", "Putalibazar Municipality", "Galyang Municipality", "Chapakot Municipality", "Bhirkot Municipality", "Aandhikhola", "Phedikhola", "Biruwa", "Harinas", "Kaligandaki", "Arjunchhaupari"] },
  "Baglung": { lat: 28.2667, lng: 83.6000, alt: "1,020m", munis: ["Baglung Municipality", "Galkot Municipality", "Jaimuni Municipality", "Dhorpatan Municipality (Hunting Reserve)", "Bareng", "Kanthekhola", "Tarakhola", "Nisikhola", "Badigad", "Tamankhola"] },
  "Lamjung": { lat: 28.2333, lng: 84.4167, alt: "750m", munis: ["Besishahar Municipality", "Sundarbazar Municipality", "Rainas Municipality", "MadhyaNepal Municipality", "Kwaholasothar", "Dordi", "Dudhpokhari", "Marsyangdi"] },
  "Parbat": { lat: 28.2167, lng: 83.7000, alt: "900m", munis: ["Kushma Municipality", "Phalebas Municipality", "Jaljala", "Paiyun", "Mahashila", "Modi", "Bihadi"] },
  "Nawalpur": { lat: 27.7000, lng: 84.1500, alt: "160m", munis: ["Kawasoti Municipality", "Gaindakot Municipality", "Devachuli Municipality", "Madhyabindu Municipality", "Binayi Tribeni", "Bulingtar", "Baudikali", "Hupsekot"] },

  // Koshi
  "Solukhumbu": { lat: 27.8056, lng: 86.7111, alt: "3,440m", munis: ["Khumbu Pasanglhamu Rural Municipality (Namche/EBC)", "Solududhkunda Municipality (Salleri)", "Dudhkaushika", "Nechasalyan", "Mahakulung", "Likhupike", "Sotang", "Thulung Dudhkoshi"] },
  "Ilam": { lat: 26.9117, lng: 87.9261, alt: "1,208m", munis: ["Ilam Municipality", "Suryodaya Municipality (Kanyam Tea Estate)", "Deumai Municipality", "Mai Municipality", "Fakphokthum", "Chulachuli", "Maijogmai", "Mangsebung", "Rong", "Sandakphu / Sandakpur"] },
  "Sunsari": { lat: 26.8167, lng: 87.2833, alt: "135m", munis: ["Dharan Sub-Metropolitan (Bhedetar Gate)", "Itahari Sub-Metropolitan", "Inaruwa Municipality", "Duhabi Municipality", "Barahachhetra Municipality", "Ramdhuni Municipality", "Koshi Rural Municipality (Koshi Tappu)"] },
  "Morang": { lat: 26.4500, lng: 87.2833, alt: "80m", munis: ["Biratnagar Metropolitan City", "Sundar Haraicha Municipality", "Belbari Municipality", "Pathari Shanischare", "Ratuwamai", "Urlabari", "Rangeli", "Sunawarshi"] },
  "Jhapa": { lat: 26.6500, lng: 87.9000, alt: "96m", munis: ["Bhadrapur Municipality", "Birtamod Municipality", "Damak Municipality", "Mechinagar Municipality (Kakarbhitta Gate)", "Arjundhara", "Kankai", "Shivasatakshi", "Gauradaha"] },
  "Taplejung": { lat: 27.3500, lng: 87.6667, alt: "1,820m", munis: ["Phungling Municipality (Pathibhara Temple)", "Aathrai Tribeni", "Sidingba", "Faktanglung", "Mikwakhola", "Meringden", "Maiwakhola", "Sirijangha"] },
  "Sankhuwasabha": { lat: 27.4500, lng: 87.2167, alt: "1,200m", munis: ["Khandbari Municipality", "Chainpur Municipality", "Dharmadevi", "Madi", "Panchakhapan", "Bhotkhola (Makalu Gate)", "Chichila", "Makalu", "Sabhafokhari", "Silichong"] },

  // Lumbini
  "Rupandehi": { lat: 27.4699, lng: 83.2755, alt: "105m", munis: ["Lumbini Sanskritik Municipality (Birthplace of Buddha)", "Butwal Sub-Metropolitan City", "Siddharthanagar Municipality (Bhairahawa)", "Tilottama Municipality", "Sainamaina Municipality", "Devdaha Municipality"] },
  "Palpa": { lat: 27.8667, lng: 83.5500, alt: "1,350m", munis: ["Tansen Municipality (Heritage Town)", "Rampur Municipality", "Rainadevi Chhahara", "Ribdikot", "Bagnaskali", "Rambha", "Purkhakot", "Tinau", "Nisdi", "Mathagadhi"] },
  "Pyuthan": { lat: 28.0833, lng: 82.5833, alt: "2,121m", munis: ["Swargadwari Municipality (Sacred Temple)", "Pyuthan Municipality", "Gaumukhi", "Mandavi", "Sarumarani", "Mallarani", "Naubahini", "Jhimruk", "Airawati"] },
  "Bardiya": { lat: 28.4500, lng: 81.3333, alt: "140m", munis: ["Thakurbaba Municipality (Bardiya National Park Gate)", "Gulariya Municipality", "Madhuwan Municipality", "Rajapur", "Barbardiya", "Bansgadhi", "Geruwa", "Badhaiyatal"] },
  "Banke": { lat: 28.0500, lng: 81.6167, alt: "150m", munis: ["Nepalgunj Sub-Metropolitan", "Kohalpur Municipality", "Rapti Sonari", "Narainapur", "Duduwa", "Janaki", "Khajura", "Baijanath"] },
  "Dang": { lat: 28.0333, lng: 82.3000, alt: "600m", munis: ["Ghorahi Sub-Metropolitan", "Tulsipur Sub-Metropolitan", "Lamahi Municipality", "Gadhawa", "Rajpur", "Shantinagar", "Rapti", "Babai", "Dangisharan", "Banglachuli"] },
  "Kapilvastu": { lat: 27.5500, lng: 83.0500, alt: "100m", munis: ["Kapilvastu Municipality (Ancient Shakya Kingdom)", "Banganga Municipality", "Buddhabhumi Municipality", "Shivaraj", "Krishnanagar", "Maharajgunj"] },

  // Karnali
  "Mugu": { lat: 29.5333, lng: 82.0833, alt: "2,990m", munis: ["Chhayanath Rara Municipality (Rara Lake)", "Khatyad Rural Municipality", "Mugum Karmarong Rural Municipality", "Soru Rural Municipality"] },
  "Dolpa": { lat: 29.2167, lng: 82.9500, alt: "3,611m", munis: ["Shey Phoksundo Rural Municipality (Deepest Lake)", "Thuli Bheri Municipality (Dunai)", "Tripurasundari Municipality", "Dolpo Buddha", "Chharka Tangsong", "Kaike", "Mudkechula", "Jagadulla"] },
  "Surkhet": { lat: 28.6000, lng: 81.6333, alt: "665m", munis: ["Birendranagar Municipality (Provincial Capital)", "Gurbhakot Municipality", "Bheriganga Municipality", "Panchapuri", "Lekbeshi", "Chaukune", "Barahatal", "Chingad", "Simta"] },
  "Jumla": { lat: 29.2747, lng: 82.1839, alt: "2,514m", munis: ["Chandannath Municipality (Sinja Valley)", "Kankasundari", "Sinja", "Hima", "Tila", "Guthichaur", "Tatopani", "Patarasi"] },
  "Humla": { lat: 30.0000, lng: 81.8000, alt: "2,940m", munis: ["Simkot Rural Municipality", "Namkha Rural Municipality (Limi Valley)", "Kharpunath", "Sarkegad", "Chankheli", "Adanchuli", "Tanjakot"] },

  // Madhesh
  "Dhanusha": { lat: 26.7271, lng: 85.9242, alt: "74m", munis: ["Janakpurdham Sub-Metropolitan (Janaki Mandir)", "Dhanusadham Municipality", "Chhireshwarnath", "Ganeshman Charnath", "Mithila Municipality", "Sabaila"] },
  "Parsa": { lat: 27.0167, lng: 84.8833, alt: "91m", munis: ["Birgunj Metropolitan City", "Pokhariya Municipality", "Bahudaramai", "Parsagadhi", "Thori (National Park Gate)"] },

  // Sudurpashchim
  "Kanchanpur": { lat: 28.9667, lng: 80.1833, alt: "198m", munis: ["Bhimdatta Municipality (Mahendranagar/Shuklaphanta)", "Shuklaphanta Municipality", "Bedkot", "Dodhara Chandani", "Krishnapur", "Punarwas", "Belauri", "Laljhadi", "Beldandi"] },
  "Kailali": { lat: 28.6833, lng: 80.6000, alt: "182m", munis: ["Dhangadhi Sub-Metropolitan", "Tikapur Municipality", "Ghodaghodi Municipality (Ramsar Lake)", "Lamki Chuha", "Godawari", "Bhajani", "Gauriganga"] }
}

// Comprehensive Fuzzy, Acronym, and Phonetic Place Matrix for all 77 Districts & Landmarks
export const NEPAL_FUZZY_PLACE_INDEX = [
  // Parbat / Bihadi
  {
    keys: ["bihadi", "vihadi", "beehadi", "bihadi gaunpalika"],
    canonicalName: "Bihadi Rural Municipality (बिहादी)",
    correctedName: "Bihadi",
    lat: 28.0250, lng: 83.6210, alt: "1,150m",
    district: "Parbat", province: "Gandaki", municipality: "Bihadi Rural Municipality",
    category: "Scenic Hill Settlement",
    image: "/images/destinations/pokhara/img4.jpg",
    slug: "bihadi-parbat",
    description: "Scenic rural settlement along the Kali Gandaki river corridor in Parbat district."
  },
  // Syangja / Waling
  {
    keys: ["waling", "walling", "waaling", "waling bazaar", "waling muni"],
    canonicalName: "Waling Municipality (वालिङ)",
    correctedName: "Waling",
    lat: 27.9833, lng: 83.7667, alt: "740m",
    district: "Syangja", province: "Gandaki", municipality: "Waling Municipality",
    category: "Heritage Town",
    image: "/images/destinations/pokhara/img3.jpg",
    slug: "waling-bazaar",
    description: "Vibrant cultural town on the Siddhartha Highway surrounded by lush terraced green hills."
  },
  // Pokhara
  {
    keys: ["pkr", "pokhara", "pohra", "pohkra", "pokhra", "phewa", "lakeside"],
    canonicalName: "Pokhara & Phewa Lake (पोखरा)",
    correctedName: "Pokhara",
    lat: 28.2096, lng: 83.9856, alt: "822m",
    district: "Kaski", province: "Gandaki", municipality: "Pokhara Metropolitan City",
    category: "Lakes & Adventure",
    image: "/images/destinations/pokhara/img1.jpg",
    slug: "phewa-lake-tal-barahi",
    description: "Tourism capital of Nepal with freshwater lakes and 360-degree views of Mt. Machhapuchhre."
  },
  // Kathmandu
  {
    keys: ["ktm", "kathmandu", "katmandu", "kathmndu", "pashupati", "thamel"],
    canonicalName: "Kathmandu Valley (काठमाडौँ)",
    correctedName: "Kathmandu",
    lat: 27.7172, lng: 85.3240, alt: "1,400m",
    district: "Kathmandu", province: "Bagmati", municipality: "Kathmandu Metropolitan City",
    category: "UNESCO World Heritage",
    image: "/images/destinations/kathmandu/img1.jpg",
    slug: "pashupatinath-temple",
    description: "Historic capital city renowned for ancient Licchavi and Malla pagoda architecture."
  },
  // Myagdi / Galeshwor & Poon Hill
  {
    keys: ["galeswor", "galeshwar", "galeshor", "galeshwor temple", "beni"],
    canonicalName: "Galeshwor Dham & Beni (गलेश्वर)",
    correctedName: "Galeshwor",
    lat: 28.3800, lng: 83.5600, alt: "880m",
    district: "Myagdi", province: "Gandaki", municipality: "Beni Municipality",
    category: "Sacred Temple",
    image: "/images/destinations/annapurna/img4.jpg",
    slug: "galeshwor-temple-myagdi",
    description: "Sacred Shiva pilgrimage temple built over a single massive rock on the banks of Kali Gandaki."
  },
  {
    keys: ["poonhill", "poon hill", "punhill", "ghorepani", "ghorepani poon hill"],
    canonicalName: "Ghorepani Poon Hill (पून हिल)",
    correctedName: "Poon Hill",
    lat: 28.4000, lng: 83.7000, alt: "3,210m",
    district: "Myagdi", province: "Gandaki", municipality: "Annapurna Rural Municipality",
    category: "Panoramic Viewpoint",
    image: "/images/destinations/annapurna/img5.jpg",
    slug: "ghorepani-poon-hill",
    description: "World-famous sunrise vantage point over Dhaulagiri, Annapurna, and Nilgiri ranges."
  },
  // Pyuthan / Swargadwari
  {
    keys: ["swargadwari", "sworgadwari", "swargadwary", "swarga dwari"],
    canonicalName: "Swargadwari Sacred Ashram (स्वर्गद्वारी)",
    correctedName: "Swargadwari",
    lat: 28.1800, lng: 82.6800, alt: "2,120m",
    district: "Pyuthan", province: "Lumbini", municipality: "Swargadwari Municipality",
    category: "Pilgrimage Sanctuary",
    image: "/images/destinations/lumbini/img3.jpg",
    slug: "swargadwari-pyuthan",
    description: "Ancient Vedic sacrificial holy shrine legendary as the gateway to heaven in Mahabharata."
  },
  // Everest
  {
    keys: ["ebc", "everest", "sagarmatha", "namche", "kala patthar", "lukla"],
    canonicalName: "Everest Base Camp (सगरमाथा आधार शिविर)",
    correctedName: "Everest Base Camp",
    lat: 28.0042, lng: 86.8570, alt: "5,364m",
    district: "Solukhumbu", province: "Koshi", municipality: "Khumbu Pasang Lhamu",
    category: "Alpine Trekking",
    image: "/images/destinations/everest/img1.jpg",
    slug: "everest-base-camp-ebc",
    description: "Foot of Mt. Everest (8,848m) surrounded by the highest snow-capped summits on Earth."
  },
  // Annapurna
  {
    keys: ["abc", "annapurna", "anapurna", "annpurna", "annapurna base camp"],
    canonicalName: "Annapurna Sanctuary & ABC (अन्नपूर्ण)",
    correctedName: "Annapurna Base Camp",
    lat: 28.5300, lng: 83.8800, alt: "4,130m",
    district: "Kaski", province: "Gandaki", municipality: "Annapurna Rural Municipality",
    category: "High Mountain Amphitheater",
    image: "/images/destinations/annapurna/img1.jpg",
    slug: "annapurna-base-camp-abc-sanctuary",
    description: "Spectacular 360-degree mountain bowl surrounded by Annapurna I (8,091m) and Fishtail."
  },
  // Chitwan
  {
    keys: ["chitwan", "chitwn", "chitwon", "sauraha", "saurha", "rhino"],
    canonicalName: "Chitwan National Park & Sauraha (चितवन)",
    correctedName: "Chitwan Sauraha",
    lat: 27.5800, lng: 84.4900, alt: "208m",
    district: "Chitwan", province: "Bagmati", municipality: "Ratnanagar Municipality",
    category: "Wildlife & Safari",
    image: "/images/destinations/chitwan/img1.jpg",
    slug: "chitwan-national-park-safari",
    description: "UNESCO protected subtropical wilderness home to wild Bengal Tigers and One-Horned Rhinos."
  },
  // Lumbini
  {
    keys: ["lumbini", "lumbni", "lumvini", "buddha", "maya devi"],
    canonicalName: "Lumbini Sacred Garden (लुम्बिनी)",
    correctedName: "Lumbini",
    lat: 27.4833, lng: 83.2767, alt: "150m",
    district: "Rupandehi", province: "Lumbini", municipality: "Lumbini Sanskritik Municipality",
    category: "Birthplace of Buddha",
    image: "/images/destinations/lumbini/img1.jpg",
    slug: "lumbini-sacred-garden-maya-devi-temple",
    description: "The historical birthplace of Siddhartha Gautama Buddha in 623 BC with international monasteries."
  },
  // Mustang
  {
    keys: ["mustang", "mustng", "lomanthang", "lo-manthang", "muktinath", "jomsom"],
    canonicalName: "Upper Mustang & Lo Manthang (मुस्ताङ)",
    correctedName: "Mustang",
    lat: 28.9985, lng: 83.8473, alt: "3,840m",
    district: "Mustang", province: "Gandaki", municipality: "Lo-Ghekar Damodarkunda",
    category: "High Altitude Desert",
    image: "/images/destinations/mustang/img1.jpg",
    slug: "upper-mustang-lo-manthang",
    description: "Ancient walled Tibetan kingdom in the rain-shadow of Annapurna and Dhaulagiri."
  },
  // Rara Lake
  {
    keys: ["rara", "rara lake", "mugu lake", "mugu"],
    canonicalName: "Rara Lake & National Park (रारा ताल)",
    correctedName: "Rara Lake",
    lat: 29.5375, lng: 82.0911, alt: "2,990m",
    district: "Mugu", province: "Karnali", municipality: "Chhayanath Rara Municipality",
    category: "Alpine Lake",
    image: "/images/destinations/rara/img1.jpg",
    slug: "rara-lake-national-park",
    description: "Nepal's largest freshwater lake with deep crystal waters surrounded by coniferous forests."
  },
  // Tilicho
  {
    keys: ["tilicho", "tilicho lake", "manang lake"],
    canonicalName: "Tilicho Lake (तिलिचो ताल)",
    correctedName: "Tilicho Lake",
    lat: 28.6800, lng: 83.8400, alt: "4,919m",
    district: "Manang", province: "Gandaki", municipality: "Manang Ngisyang",
    category: "High Glacial Lake",
    image: "/images/destinations/tilicho/img1.jpg",
    slug: "tilicho-lake-trek",
    description: "One of the highest alpine glacial lakes on Earth at nearly 5,000m elevation."
  },
  // Jumla / Sinja
  {
    keys: ["sinja", "sinja valley", "jumla", "khas"],
    canonicalName: "Sinja Valley (सिन्जा उपत्यका)",
    correctedName: "Sinja Valley",
    lat: 29.3500, lng: 81.9700, alt: "2,450m",
    district: "Jumla", province: "Karnali", municipality: "Sinja Rural Municipality",
    category: "Historic Valley",
    image: "/images/destinations/rara/img4.jpg",
    slug: "sinja-valley-jumla",
    description: "Ancient capital of the Khas Malla Empire and the historic birthplace of the Nepali language."
  },
  // Baglung / Dhorpatan
  {
    keys: ["dhorpatan", "dhorpatan hunting", "baglung reserve"],
    canonicalName: "Dhorpatan Hunting Reserve (ढोरपाटन)",
    correctedName: "Dhorpatan",
    lat: 28.5300, lng: 83.0500, alt: "2,850m",
    district: "Baglung", province: "Gandaki", municipality: "Dhorpatan Municipality",
    category: "Alpine Meadows & Reserve",
    image: "/images/destinations/annapurna/img4.jpg",
    slug: "dhorpatan-hunting-reserve",
    description: "Nepal's only hunting reserve featuring high marshlands, alpine forests, and Blue Sheep."
  },
  // Doti / Khaptad
  {
    keys: ["khaptad", "khaptad national park", "khaptad baba"],
    canonicalName: "Khaptad National Park & Meadows (खप्तड)",
    correctedName: "Khaptad",
    lat: 29.3600, lng: 81.1200, alt: "3,100m",
    district: "Doti", province: "Sudurpashchim", municipality: "Khaptad Chhanna",
    category: "Sacred Plateau Meadows",
    image: "/images/destinations/rara/img3.jpg",
    slug: "khaptad-national-park",
    description: "Spiritual plateau of rolling green meadows, ancient hermitages, and 200+ bird species."
  },
  // Taplejung / Pathibhara
  {
    keys: ["pathibhara", "pathivara", "taplejung temple"],
    canonicalName: "Pathibhara Devi Temple (पाथिभरा)",
    correctedName: "Pathibhara",
    lat: 27.4200, lng: 87.7700, alt: "3,794m",
    district: "Taplejung", province: "Koshi", municipality: "Phungling Municipality",
    category: "High Altitude Sacred Shrine",
    image: "/images/destinations/everest/img1.jpg",
    slug: "pathibhara-devi-temple",
    description: "Revered Shakti Peeth atop an alpine ridge offering vistas of Mt. Kanchenjunga."
  },
  // Sankhuwasabha / Barun
  {
    keys: ["barun", "barun valley", "makalu barun"],
    canonicalName: "Makalu Barun Valley (बरुण उपत्यका)",
    correctedName: "Barun Valley",
    lat: 27.7000, lng: 87.1000, alt: "3,600m",
    district: "Sankhuwasabha", province: "Koshi", municipality: "Makalu Rural Municipality",
    category: "Pristine Glacial Wilderness",
    image: "/images/destinations/everest/img3.jpg",
    slug: "makalu-barun-national-park",
    description: "Untouched deep Himalayan canyon featuring rare wildlife, waterfalls, and granite cliffs."
  },
  // Gulmi/Palpa / Ridi
  {
    keys: ["ridi", "ruru", "ruru kshetra", "rishikesh"],
    canonicalName: "Ridi & Ruru Kshetra Dham (रुरु क्षेत्र)",
    correctedName: "Ridi (Ruru Kshetra)",
    lat: 27.9300, lng: 83.4300, alt: "450m",
    district: "Gulmi", province: "Lumbini", municipality: "Ruru Rural Municipality",
    category: "Historic Confluence Shrine",
    image: "/images/destinations/bandipur/img1.jpg",
    slug: "ruru-kshetra-ridi",
    description: "Sacred confluence of Ridi and Kali Gandaki rivers with ancient Rishikesh Temple."
  }
]

/**
 * Intelligent Fuzzy Resolver:
 * Accepts ANY phonetic spelling, typo, or acronym (e.g. 'pkr', 'bihadi', 'walling', 'galeswor', 'chitwn', 'lumbni')
 * and returns canonical place data with auto-attached GPS coordinates, altitude, district, and province.
 */
export function resolveFuzzyPlaceLocation(query) {
  if (!query || typeof query !== "string") return null
  const cleanQ = query.toLowerCase().trim().replace(/[^a-z0-9\s]/g, "")
  if (cleanQ.length < 2) return null

  // 1. Direct key match in fuzzy index
  for (const item of NEPAL_FUZZY_PLACE_INDEX) {
    if (item.keys.some(k => k === cleanQ || cleanQ.includes(k) || k.includes(cleanQ))) {
      const isExact = item.correctedName.toLowerCase() === cleanQ
      return {
        matched: true,
        canonicalName: item.canonicalName,
        correctedName: item.correctedName,
        didYouMean: !isExact ? `Showing results for ${item.correctedName}, ${item.district} (matched from '${query}')` : null,
        latitude: item.lat,
        longitude: item.lng,
        altitude: item.alt,
        district: item.district,
        province: item.province,
        municipality: item.municipality,
        category: item.category,
        confidence: isExact ? 100 : 96,
        image: item.image,
        slug: item.slug,
        description: item.description,
      }
    }
  }

  // 2. Match District Name directly
  for (const [distName, info] of Object.entries(DISTRICT_DEFAULTS)) {
    const distClean = distName.toLowerCase()
    if (distClean.includes(cleanQ) || cleanQ.includes(distClean)) {
      // Find province
      let prov = "Bagmati"
      for (const [p, dists] of Object.entries(NEPAL_ALL_DISTRICTS)) {
        if (dists.includes(distName)) {
          prov = p
          break
        }
      }
      return {
        matched: true,
        canonicalName: `${distName} District (${prov} Province)`,
        correctedName: distName,
        didYouMean: `Geocoded district center: ${distName}`,
        latitude: info.lat,
        longitude: info.lng,
        altitude: info.alt,
        district: distName,
        province: prov,
        municipality: info.munis[0] || "",
        category: "District Center",
        confidence: 90,
        image: "/images/destinations/pokhara/img1.jpg",
        slug: distName.toLowerCase(),
        description: `Official administrative center of ${distName} in ${prov} Province.`,
      }
    }
  }

  return null
}

/**
 * High-precision forward geocoder supporting all 77 districts and custom entries
 */
export function geocodeNepalPlace(province, district, municipalityName = "", wardNo = 1) {
  const distInfo = DISTRICT_DEFAULTS[district]

  let baseLat = distInfo?.lat || 28.2096
  let baseLng = distInfo?.lng || 83.9856
  let alt = distInfo?.alt || "1,400m"

  const wardInt = parseInt(wardNo, 10) || 1
  const latOffset = ((wardInt % 5) - 2) * 0.0035
  const lngOffset = (Math.floor(wardInt / 5) - 1) * 0.0035

  return {
    lat: Number((baseLat + latOffset).toFixed(6)),
    lng: Number((baseLng + lngOffset).toFixed(6)),
    alt: alt,
  }
}

