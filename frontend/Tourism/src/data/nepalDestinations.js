// A sample dataset of real Nepal destinations used as a local fallback so the
// Explore/Recommendation/Trip Planner pages have rich content (images, budget
// estimates, heritage info) even before the backend dataset is fully wired up.
// Once the backend's `/destinations` and `/recommendations` endpoints return
// data, that data takes priority — this file is only used as a fallback.

const nepalDestinations = [
  {
    id: "np-ktm-durbar",
    name: "Kathmandu Durbar Square",
    location: "Kathmandu, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.7,
    price: 15,
    image: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=700",
    gallery: [
      "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=500",
      "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?w=500",
    ],
    description:
      "A UNESCO World Heritage Site featuring ancient palaces, courtyards and temples that once housed Nepal's royal families.",
    localLanguage: "Nepali, Newari",
    heritageDescription:
      "Home to the Hanuman Dhoka Palace complex, the Kumari Ghar (residence of the Living Goddess), and dozens of pagoda-style temples dating back to the Malla era.",
    heritageSites: [
      { name: "Hanuman Dhoka Palace", image: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400" },
      { name: "Kumari Ghar", image: "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?w=400" },
      { name: "Taleju Temple", image: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=400" },
    ],
    coordinates: { lat: 27.7040, lng: 85.3070 },
  },
  {
    id: "np-pokhara-phewa",
    name: "Phewa Lake, Pokhara",
    location: "Pokhara, Gandaki Province",
    category: "lakes",
    isHeritage: false,
    rating: 4.8,
    price: 25,
    image: "https://images.unsplash.com/photo-1544967082-d9d25d867d66?w=700",
    gallery: [
      "https://images.unsplash.com/photo-1571401835393-8c5f35328320?w=500",
      "https://images.unsplash.com/photo-1602088113235-229c19758e9c?w=500",
    ],
    description:
      "A serene lake framed by the Annapurna range, popular for boating, lakeside cafes, and views of the Machapuchare peak reflected on the water.",
    localLanguage: "Nepali, Gurung",
    coordinates: { lat: 28.2096, lng: 83.9856 },
  },
  {
    id: "np-chitwan",
    name: "Chitwan National Park",
    location: "Chitwan, Bagmati Province",
    category: "adventure",
    isHeritage: false,
    rating: 4.6,
    price: 60,
    image: "https://images.unsplash.com/photo-1549366021-9f761d450615?w=700",
    gallery: [
      "https://images.unsplash.com/photo-1583212292454-1fe6229603b7?w=500",
    ],
    description:
      "A UNESCO World Heritage jungle reserve known for one-horned rhino and Bengal tiger safaris, canoe rides, and Tharu cultural villages.",
    localLanguage: "Tharu, Nepali",
    coordinates: { lat: 27.5291, lng: 84.3542 },
  },
  {
    id: "np-lumbini",
    name: "Lumbini",
    location: "Lumbini, Province No. 5",
    category: "heritage",
    isHeritage: true,
    rating: 4.9,
    price: 20,
    image: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=700",
    description:
      "The birthplace of Lord Buddha, home to the sacred Maya Devi Temple and monasteries built by Buddhist communities from around the world.",
    localLanguage: "Awadhi, Bhojpuri, Nepali",
    heritageDescription:
      "A UNESCO World Heritage pilgrimage site with the Ashoka Pillar, the sacred garden, and the eternal flame for world peace.",
    heritageSites: [
      { name: "Maya Devi Temple", image: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=400" },
      { name: "Ashoka Pillar", image: "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?w=400" },
    ],
    coordinates: { lat: 27.4833, lng: 83.2767 },
  },
  {
    id: "np-everest-base-camp",
    name: "Everest Base Camp Trek",
    location: "Solukhumbu, Province No. 1",
    category: "adventure",
    isHeritage: false,
    rating: 4.9,
    price: 900,
    image: "https://images.unsplash.com/photo-1544198365-f5d60b6d8190?w=700",
    description:
      "A multi-day trek through Sherpa villages, suspension bridges, and Himalayan monasteries to the base of the world's tallest mountain.",
    localLanguage: "Sherpa, Nepali",
    coordinates: { lat: 27.9881, lng: 86.9250 },
  },
  {
    id: "np-bhaktapur",
    name: "Bhaktapur Durbar Square",
    location: "Bhaktapur, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.8,
    price: 15,
    image: "https://images.unsplash.com/photo-1590766940554-153d9e0b2eff?w=700",
    description:
      "A beautifully preserved medieval city known for pottery squares, wood carvings, and the iconic Nyatapola Temple.",
    localLanguage: "Newari, Nepali",
    heritageDescription:
      "The best-preserved of Kathmandu Valley's three durbar squares, famous for its Peacock Window and traditional pottery-making community.",
    heritageSites: [
      { name: "Nyatapola Temple", image: "https://images.unsplash.com/photo-1590766940554-153d9e0b2eff?w=400" },
      { name: "Pottery Square", image: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400" },
    ],
    coordinates: { lat: 27.6710, lng: 85.4298 },
  },
  {
    id: "np-mustang",
    name: "Upper Mustang",
    location: "Mustang, Gandaki Province",
    category: "adventure",
    isHeritage: true,
    rating: 4.7,
    price: 450,
    image: "https://images.unsplash.com/photo-1626621331169-5f34be280ed9?w=700",
    description:
      "A remote former kingdom with dramatic desert-like cliffs, ancient cave monasteries, and the walled city of Lo Manthang.",
    localLanguage: "Tibetan, Nepali",
    coordinates: { lat: 29.1867, lng: 83.9642 },
  },
  {
    id: "np-rara",
    name: "Rara Lake",
    location: "Mugu, Karnali Province",
    category: "lakes",
    isHeritage: false,
    rating: 4.6,
    price: 300,
    image: "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=700",
    description:
      "Nepal's largest lake, tucked inside Rara National Park — remote, pristine, and surrounded by pine forest.",
    localLanguage: "Nepali",
    coordinates: { lat: 29.5330, lng: 82.0850 },
  },
  {
    id: "np-patan",
    name: "Patan Durbar Square",
    location: "Lalitpur, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.8,
    price: 15,
    image: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=700",
    description:
      "Known as the city of fine arts, famed for intricate metal and stone craftsmanship and the Patan Museum.",
    localLanguage: "Newari, Nepali",
    heritageDescription:
      "One of the three medieval royal cities of the Kathmandu Valley, celebrated for its Krishna Mandir and traditional Newari architecture.",
    heritageSites: [
      { name: "Krishna Mandir", image: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=400" },
      { name: "Patan Museum", image: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400" },
    ],
    coordinates: { lat: 27.6727, lng: 85.3247 },
  },
  {
    id: "np-annapurna",
    name: "Annapurna Base Camp Trek",
    location: "Kaski, Gandaki Province",
    category: "adventure",
    isHeritage: false,
    rating: 4.9,
    price: 550,
    image: "https://images.unsplash.com/photo-1585511582812-88478e0a2705?w=700",
    description:
      "A classic trek through rhododendron forests and Gurung villages, ending in a natural amphitheater surrounded by 7,000m peaks.",
    localLanguage: "Gurung, Nepali",
    coordinates: { lat: 28.5309, lng: 83.8792 },
  },
  {
    id: "np-janakpur",
    name: "Janakpur (Janaki Mandir)",
    location: "Dhanusha, Madhesh Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.5,
    price: 10,
    image: "https://images.unsplash.com/photo-1548013146-72479768bada?w=700",
    description:
      "A major Hindu pilgrimage city and birthplace of Goddess Sita, famous for the ornate white Janaki Mandir temple.",
    localLanguage: "Maithili, Bhojpuri, Nepali",
    heritageDescription:
      "The Janaki Mandir blends Mughal and Rajput architectural styles and hosts the annual Vivaha Panchami celebration.",
    heritageSites: [
      { name: "Janaki Mandir", image: "https://images.unsplash.com/photo-1548013146-72479768bada?w=400" },
    ],
    coordinates: { lat: 26.7288, lng: 85.9247 },
  },
  {
    id: "np-ilam",
    name: "Ilam Tea Gardens",
    location: "Ilam, Koshi Province",
    category: "nature",
    isHeritage: false,
    rating: 4.6,
    price: 40,
    image: "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=700",
    description:
      "Rolling green tea estates in the eastern hills, known for organic tea production and misty mountain views.",
    localLanguage: "Nepali, Limbu, Rai",
    coordinates: { lat: 26.9088, lng: 87.9257 },
  },
]

export default nepalDestinations

export const searchDestinations = (query = "", category = "") => {
  const q = query.trim().toLowerCase()
  return nepalDestinations.filter((d) => {
    const matchesQuery =
      !q ||
      d.name.toLowerCase().includes(q) ||
      d.location.toLowerCase().includes(q) ||
      d.category.toLowerCase().includes(q)
    const matchesCategory = !category || d.category === category
    return matchesQuery && matchesCategory
  })
}

export const getDestinationById = (id) => nepalDestinations.find((d) => d.id === id)