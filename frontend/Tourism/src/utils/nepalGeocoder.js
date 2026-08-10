/**
 * Nepal Administrative Geocoder & Municipality/Ward Coordinate Calculator
 * Computes estimated Latitude, Longitude, and Altitude based on Nepal's
 * 7 Provinces, 77 Districts, Municipalities, and local Ward Numbers.
 */

export const NEPAL_ADMIN_DIVISIONS = {
  "Bagmati": {
    districts: {
      "Kathmandu": {
        municipalities: [
          { name: "Kathmandu Metropolitan City", lat: 27.7172, lng: 85.3240, alt: "1,400m", wards: 32 },
          { name: "Kirtipur Municipality", lat: 27.6797, lng: 85.2754, alt: "1,420m", wards: 10 },
          { name: "Budhanilkantha Municipality", lat: 27.7788, lng: 85.3606, alt: "1,480m", wards: 13 },
          { name: "Chandragiri Municipality", lat: 27.6933, lng: 85.2155, alt: "1,550m", wards: 15 },
          { name: "Tokha Municipality", lat: 27.7554, lng: 85.3262, alt: "1,430m", wards: 11 },
          { name: "Gokarneshwor Municipality", lat: 27.7478, lng: 85.3986, alt: "1,450m", wards: 9 },
          { name: "Nagarjun Municipality", lat: 27.7314, lng: 85.2572, alt: "1,480m", wards: 10 },
        ]
      },
      "Bhaktapur": {
        municipalities: [
          { name: "Bhaktapur Municipality", lat: 27.6710, lng: 85.4298, alt: "1,401m", wards: 10 },
          { name: "Changunarayan Municipality", lat: 27.7126, lng: 85.4282, alt: "1,540m", wards: 9 },
          { name: "Madhyapur Thimi Municipality", lat: 27.6833, lng: 85.3833, alt: "1,380m", wards: 9 },
          { name: "Suryabinayak Municipality", lat: 27.6583, lng: 85.4167, alt: "1,420m", wards: 10 },
        ]
      },
      "Lalitpur": {
        municipalities: [
          { name: "Lalitpur Metropolitan City", lat: 27.6644, lng: 85.3188, alt: "1,400m", wards: 29 },
          { name: "Godawari Municipality", lat: 27.5956, lng: 85.3814, alt: "1,520m", wards: 14 },
          { name: "Mahalaxmi Municipality", lat: 27.6500, lng: 85.3667, alt: "1,410m", wards: 10 },
        ]
      },
      "Chitwan": {
        municipalities: [
          { name: "Bharatpur Metropolitan City", lat: 27.6833, lng: 84.4333, alt: "208m", wards: 29 },
          { name: "Ratnanagar Municipality (Sauraha)", lat: 27.6167, lng: 84.5167, alt: "150m", wards: 16 },
          { name: "Kalika Municipality", lat: 27.6833, lng: 84.5667, alt: "230m", wards: 11 },
          { name: "Madi Municipality", lat: 27.4667, lng: 84.3500, alt: "160m", wards: 9 },
        ]
      },
      "Rasuwa": {
        municipalities: [
          { name: "Gosaikunda Rural Municipality", lat: 28.2117, lng: 85.5683, alt: "3,870m", wards: 6 },
          { name: "Kalika Rural Municipality", lat: 28.0500, lng: 85.2500, alt: "1,950m", wards: 5 },
          { name: "Naukunda Rural Municipality", lat: 27.9833, lng: 85.3000, alt: "1,800m", wards: 6 },
          { name: "Uttargaya Rural Municipality", lat: 28.0167, lng: 85.2000, alt: "1,400m", wards: 5 },
        ]
      },
    }
  },
  "Gandaki": {
    districts: {
      "Kaski": {
        municipalities: [
          { name: "Pokhara Metropolitan City", lat: 28.2096, lng: 83.9856, alt: "822m", wards: 33 },
          { name: "Annapurna Rural Municipality (Ghandruk/ABC)", lat: 28.3744, lng: 83.8089, alt: "2,012m", wards: 11 },
          { name: "Machhapuchhre Rural Municipality", lat: 28.3667, lng: 83.9667, alt: "1,450m", wards: 9 },
          { name: "Madi Rural Municipality", lat: 28.3167, lng: 84.1167, alt: "1,200m", wards: 12 },
          { name: "Rupa Rural Municipality", lat: 28.1500, lng: 84.1333, alt: "900m", wards: 7 },
        ]
      },
      "Mustang": {
        municipalities: [
          { name: "Gharapjhong Rural Municipality (Jomsom/Marpha)", lat: 28.7833, lng: 83.7333, alt: "2,743m", wards: 5 },
          { name: "Baragung Muktikshetra (Muktinath/Kagbeni)", lat: 28.8167, lng: 83.8667, alt: "3,800m", wards: 5 },
          { name: "Lo-Ghekar Damodarkunda (Charang)", lat: 29.0500, lng: 83.9333, alt: "3,560m", wards: 5 },
          { name: "Lo Manthang Rural Municipality (Walled City)", lat: 29.1822, lng: 83.9567, alt: "3,840m", wards: 5 },
          { name: "Thasang Rural Municipality (Lete/Kobang)", lat: 28.6333, lng: 83.6000, alt: "2,480m", wards: 5 },
        ]
      },
      "Tanahun": {
        municipalities: [
          { name: "Bandipur Rural Municipality", lat: 27.9333, lng: 84.4167, alt: "1,030m", wards: 6 },
          { name: "Byas Municipality (Damauli)", lat: 27.9667, lng: 84.2833, alt: "520m", wards: 14 },
          { name: "Shuklagandaki Municipality", lat: 28.0333, lng: 84.0500, alt: "650m", wards: 12 },
          { name: "Bhimad Municipality", lat: 27.9167, lng: 84.0833, alt: "480m", wards: 9 },
        ]
      },
      "Manang": {
        municipalities: [
          { name: "Manang Disyang Rural Municipality (Manang/Tilicho)", lat: 28.6667, lng: 84.0167, alt: "3,519m", wards: 9 },
          { name: "Chame Rural Municipality (District HQ)", lat: 28.5500, lng: 84.2333, alt: "2,670m", wards: 5 },
          { name: "Narpa Bhumi Rural Municipality (Nar/Phu)", lat: 28.7833, lng: 84.2833, alt: "4,110m", wards: 5 },
        ]
      },
    }
  },
  "Koshi": {
    districts: {
      "Solukhumbu": {
        municipalities: [
          { name: "Khumbu Pasanglhamu Rural Municipality (Namche/EBC)", lat: 27.8056, lng: 86.7111, alt: "3,440m", wards: 5 },
          { name: "Solududhkunda Municipality (Salleri)", lat: 27.5000, lng: 86.5833, alt: "2,162m", wards: 11 },
          { name: "Dudhkaushika Rural Municipality", lat: 27.4167, lng: 86.7167, alt: "1,750m", wards: 9 },
        ]
      },
      "Ilam": {
        municipalities: [
          { name: "Ilam Municipality", lat: 26.9117, lng: 87.9261, alt: "1,208m", wards: 12 },
          { name: "Suryodaya Municipality (Kanyam Tea Estate)", lat: 26.8833, lng: 88.0667, alt: "1,600m", wards: 14 },
          { name: "Deumai Municipality", lat: 26.9667, lng: 87.8333, alt: "1,450m", wards: 9 },
          { name: "Mai Municipality", lat: 26.7500, lng: 87.9167, alt: "450m", wards: 10 },
        ]
      },
    }
  },
  "Lumbini": {
    districts: {
      "Rupandehi": {
        municipalities: [
          { name: "Lumbini Sanskritik Municipality (Birthplace)", lat: 27.4699, lng: 83.2755, alt: "105m", wards: 13 },
          { name: "Butwal Sub-Metropolitan City", lat: 27.7000, lng: 83.4500, alt: "210m", wards: 19 },
          { name: "Siddharthanagar Municipality (Bhairahawa)", lat: 27.5000, lng: 83.4500, alt: "110m", wards: 13 },
        ]
      },
      "Palpa": {
        municipalities: [
          { name: "Tansen Municipality (Heritage Hill Station)", lat: 27.8667, lng: 83.5500, alt: "1,350m", wards: 14 },
          { name: "Rampur Municipality", lat: 27.8667, lng: 83.8833, alt: "450m", wards: 10 },
        ]
      },
    }
  },
  "Karnali": {
    districts: {
      "Mugu": {
        municipalities: [
          { name: "Chhayanath Rara Municipality (Rara Lake)", lat: 29.5333, lng: 82.0833, alt: "2,990m", wards: 14 },
          { name: "Khatyad Rural Municipality", lat: 29.4167, lng: 81.9167, alt: "2,100m", wards: 11 },
          { name: "Mugum Karmarong Rural Municipality", lat: 29.6833, lng: 82.4167, alt: "3,400m", wards: 9 },
        ]
      },
      "Dolpa": {
        municipalities: [
          { name: "Shey Phoksundo Rural Municipality (Lake)", lat: 29.2167, lng: 82.9500, alt: "3,611m", wards: 9 },
          { name: "Thuli Bheri Municipality (Dunai)", lat: 28.9333, lng: 82.8833, alt: "2,140m", wards: 11 },
        ]
      },
    }
  },
  "Madhesh": {
    districts: {
      "Dhanusha": {
        municipalities: [
          { name: "Janakpurdham Sub-Metropolitan (Janaki Mandir)", lat: 26.7271, lng: 85.9242, alt: "74m", wards: 25 },
          { name: "Dhanusadham Municipality", lat: 26.8333, lng: 86.0333, alt: "85m", wards: 9 },
        ]
      },
    }
  },
  "Sudurpashchim": {
    districts: {
      "Kanchanpur": {
        municipalities: [
          { name: "Bhimdatta Municipality (Mahendranagar/Shuklaphanta)", lat: 28.9667, lng: 80.1833, alt: "198m", wards: 19 },
          { name: "Shuklaphanta Municipality", lat: 28.8833, lng: 80.3667, alt: "185m", wards: 12 },
        ]
      },
    }
  }
}

/**
 * Calculates geocoded coordinates based on selected administrative unit and ward.
 */
export function geocodeNepalPlace(province, district, municipalityName, wardNo = 1) {
  const provData = NEPAL_ADMIN_DIVISIONS[province]
  if (!provData) return { lat: 28.2096, lng: 83.9856, alt: "1,400m" }

  const distData = provData.districts[district]
  if (!distData) return { lat: 28.2096, lng: 83.9856, alt: "1,400m" }

  const muni = distData.municipalities.find(
    (m) => m.name.toLowerCase() === municipalityName.toLowerCase() || m.name.includes(municipalityName)
  ) || distData.municipalities[0]

  if (!muni) return { lat: 28.2096, lng: 83.9856, alt: "1,400m" }

  // Apply deterministic micro-offset based on ward number for high resolution
  const wardInt = parseInt(wardNo, 10) || 1
  const latOffset = ((wardInt % 5) - 2) * 0.003
  const lngOffset = (Math.floor(wardInt / 5) - 1) * 0.003

  return {
    lat: Number((muni.lat + latOffset).toFixed(6)),
    lng: Number((muni.lng + lngOffset).toFixed(6)),
    alt: muni.alt,
  }
}
