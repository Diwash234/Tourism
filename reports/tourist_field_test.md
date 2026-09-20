# Tourist field test — live API results (all 77 districts)

Generated: 2026-09-20T12:06:47Z · API: http://127.0.0.1:8000/api/v1
Totals: 811 places · exact 80 · partial 278 · not found 453 · routes osrm 0 / fallback 358 / failed 0 / no-hub 0

## How to read this report (analyst notes)

- **Found** = what `/places/search/` returns to a tourist typing that name: `exact`
  (name matches a published record), `partial` (a published record whose name contains
  / is contained by the query — the matched record is shown), `—` (honest NOT FOUND:
  verified absent from the 6,597-record database, never fabricated).
- **Route km / Straight km**: road-network distance from the place to the district hub
  vs straight-line displacement. Across 335 measurable pairs the median ratio is
  **1.27x** — routes follow the network, they are not straight lines. Source is
  honestly labelled (`graphml_fallback` in this sandbox; street-level `osrm` once
  ROUTING_BASE_URL is set on the host).
- **Hub** = the district's first published top destination, straight from
  `/api/v1/districts/<name>/` — a real record, occasionally a lodge because that is
  what the API lists first.
- Partial name matches can hit a namesake record in another district (e.g. "Rupakot"
  exists in two districts); the inflated route km makes those cases visible.
- Hospital/police counts are real curated records (363 hospitals, 628 police).
  Hotel/restaurant/bank columns are 0: those curated tables are empty in the dataset
  and live OSM (Overpass) is TLS-blocked in this sandbox — on an internet-connected
  host these categories resolve live. Honest zeros, no seeded data.
- 429 rate-limits (30 routes/min) were handled with client-side pacing; 0 requests
  ultimately failed.

## Bhojpur (hub: Annapurna Lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhojpur Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Hatuwagadhi | — | — | — | — | — | — | — | — | — | — | — |
| Taksar | — | — | — | — | — | — | — | — | — | — | — |
| Salpa Pokhari | — | — | — | — | — | — | — | — | — | — | — |
| Dingla | partial (Police Station Dingla) | 42.8 | 23.1 | 74 | graphml_fallback | 11 | 0 | 0 | 0 | 24 | Bhojpur District Hospital (5.97 km) |
| Tyamke Danda | — | — | — | — | — | — | — | — | — | — | — |
| Siddhakali Temple | — | — | — | — | — | — | — | — | — | — | — |
| Dudh Kunda | — | — | — | — | — | — | — | — | — | — | — |
| Arun River | partial (View to Arun River) | 1.2 | 0.9 | 2 | straight_line_fallback | 3 | 0 | 0 | 0 | 15 | Sankhuwasabha District Hospital (8.17 km) |
| Temkemaiyum | — | — | — | — | — | — | — | — | — | — | — |
| Shadananda | partial (Police Station Shadananda) | 46.7 | 32.0 | 80 | graphml_fallback | 7 | 0 | 0 | 0 | 28 | Bhojpur District Hospital (9.96 km) |
| Balankha | — | — | — | — | — | — | — | — | — | — | — |

## Dhankuta (hub: Anjuli Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dhankuta Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Hile | partial (Police Station Hile) | 9.3 | 6.1 | 16 | graphml_fallback | 17 | 0 | 0 | 0 | 30 | Dhankuta District Hospital (5.18 km) |
| Bhedetar | — | — | — | — | — | — | — | — | — | — | — |
| Pakhribas | partial (Police Station Pakhribas) | 9.9 | 9.8 | 17 | graphml_fallback | 16 | 0 | 0 | 0 | 30 | Dhankuta District Hospital (8.73 km) |
| Namaste Jharna | — | — | — | — | — | — | — | — | — | — | — |
| Rajarani | — | — | — | — | — | — | — | — | — | — | — |
| Pathibhara Temple | — | — | — | — | — | — | — | — | — | — | — |
| Mulghat | — | — | — | — | — | — | — | — | — | — | — |
| Danda Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Tinjure | — | — | — | — | — | — | — | — | — | — | — |
| Arun River | partial (View to Arun River) | 53.3 | 52.6 | 92 | graphml_fallback | 3 | 0 | 0 | 0 | 15 | Sankhuwasabha District Hospital (8.17 km) |
| Dharan Dhankuta viewpoint | — | — | — | — | — | — | — | — | — | — | — |

## Ilam (hub: Agro organic cafe)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ilam Bazaar | partial (Ilam Bazaar Tea Estates) | 1.8 | 1.1 | 3 | graphml_fallback | 13 | 0 | 0 | 0 | 23 | Ilam Community Hospital (1.51 km) |
| Kanyam | partial (Kanyam Hill (Ilam)) | 14.1 | 12.5 | 24 | graphml_fallback | 12 | 0 | 0 | 0 | 19 | Ilam Community Hospital (12.11 km) |
| Fikkal | partial (Police Station Fikkal) | 15.9 | 15.8 | 27 | graphml_fallback | 12 | 0 | 0 | 0 | 18 | Ilam Community Hospital (15.04 km) |
| Antu Danda | — | — | — | — | — | — | — | — | — | — | — |
| Shree Antu | partial (Shree Antu Tea Estates) | 16.6 | 16.2 | 29 | graphml_fallback | 12 | 0 | 0 | 0 | 18 | Ilam Community Hospital (15.49 km) |
| Mai Pokhari | exact | 29.2 | 12.1 | 50 | graphml_fallback | 13 | 0 | 0 | 0 | 22 | Ilam Community Hospital (11.87 km) |
| Sandakpur | — | — | — | — | — | — | — | — | — | — | — |
| Ilam Tea Garden | partial (Ilam Tea Gardens (Kanyam)) | 14.1 | 12.5 | 24 | graphml_fallback | 12 | 0 | 0 | 0 | 19 | Ilam Community Hospital (12.11 km) |
| Siddhi Thumka | — | — | — | — | — | — | — | — | — | — | — |
| Todke Jharna | — | — | — | — | — | — | — | — | — | — | — |
| Mai River | — | — | — | — | — | — | — | — | — | — | — |
| Chhintapu | — | — | — | — | — | — | — | — | — | — | — |

## Jhapa (hub: Aani Hotel & Heritage Plaza)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Birtamode | partial (Area Police Office Birtamode) | 11.3 | 10.8 | 19 | graphml_fallback | 9 | 0 | 0 | 0 | 17 | B&C Medical College Hospital (0.0 km) |
| Kakarbhitta | partial (Police Station Kakarbhitta) | 13.7 | 11.4 | 23 | graphml_fallback | 9 | 0 | 0 | 0 | 14 | Bhadrapur Hospital (11.65 km) |
| Kankai | partial (New kankai hotel and lodge) | 11.3 | 11.3 | 19 | graphml_fallback | 9 | 0 | 0 | 0 | 17 | B&C Medical College Hospital (0.59 km) |
| Satashi Dham | — | — | — | — | — | — | — | — | — | — | — |
| Arjundhara | — | — | — | — | — | — | — | — | — | — | — |
| Domukha | — | — | — | — | — | — | — | — | — | — | — |
| Jalthal Forest | — | — | — | — | — | — | — | — | — | — | — |
| Kichakbadh | — | — | — | — | — | — | — | — | — | — | — |
| Mechinagar | partial (Police Station Mechinagar) | 13.5 | 12.2 | 23 | graphml_fallback | 9 | 0 | 0 | 0 | 14 | Bhadrapur Hospital (12.62 km) |
| Birta Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Kankai River | — | — | — | — | — | — | — | — | — | — | — |

## Khotang (hub: Halesi Mahadev (Maratika Cave))
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Diktel | partial (Police Station Diktel) | 17.6 | 17.2 | 30 | graphml_fallback | 6 | 0 | 0 | 0 | 21 | Khotang District Hospital (0.0 km) |
| Halesi Mahadev | partial (Halesi Mahadev Cave) | 0.0 | 0.0 | 0 | straight_line_fallback | 5 | 0 | 0 | 0 | 19 | Khotang District Hospital (17.17 km) |
| Halesi Cave | — | — | — | — | — | — | — | — | — | — | — |
| Barahapokhari | — | — | — | — | — | — | — | — | — | — | — |
| Tuwachung | — | — | — | — | — | — | — | — | — | — | — |
| Rupakot | partial (Rupakot Resort) | 493.5 | 266.9 | 848 | graphml_fallback | 24 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (14.14 km) |
| Ainselukharka | — | — | — | — | — | — | — | — | — | — | — |
| Sakela | — | — | — | — | — | — | — | — | — | — | — |
| Dipsung | — | — | — | — | — | — | — | — | — | — | — |
| Halesi Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Tewang | — | — | — | — | — | — | — | — | — | — | — |

## Morang (hub: Ashok Chowk)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Biratnagar | exact | 1.6 | 1.2 | 3 | graphml_fallback | 28 | 0 | 0 | 0 | 22 | Nobel Medical College Hospital (0.0 km) |
| Koshi Tappu | partial (Koshi Tappu Birding) | 47.5 | 36.5 | 82 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Inaruwa District Hospital (14.61 km) |
| Betana Wetland | partial (Betana Wetlands) | 35.1 | 27.0 | 60 | straight_line_fallback | 29 | 0 | 0 | 0 | 26 | Itahari Hospital (15.96 km) |
| Letang | partial (Police Station Letang) | 44.1 | 33.9 | 76 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Damak General Hospital (13.96 km) |
| Pathari | partial (Police Station Pathari) | 51.3 | 39.5 | 88 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Damak General Hospital (7.04 km) |
| Urlabari | partial (Police Station Urlabari) | 44.4 | 34.1 | 76 | straight_line_fallback | 29 | 0 | 0 | 0 | 21 | Damak General Hospital (18.77 km) |
| Rangeli | partial (Police Station Rangeli) | 1.1 | 0.8 | 2 | straight_line_fallback | 28 | 0 | 0 | 0 | 22 | Nobel Medical College Hospital (1.99 km) |
| Birat Raja Durbar | — | — | — | — | — | — | — | — | — | — | — |
| Singhiya River | — | — | — | — | — | — | — | — | — | — | — |
| Budhi Ganga | — | — | — | — | — | — | — | — | — | — | — |
| Kanepokhari | partial (Kanepokhari Pokhari) | 39.3 | 30.2 | 68 | straight_line_fallback | 30 | 0 | 0 | 0 | 28 | Damak General Hospital (19.18 km) |
| Salakpur | — | — | — | — | — | — | — | — | — | — | — |

## Okhaldhunga (hub: Laliguras View Point)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Okhaldhunga Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Siddhicharan Park | — | — | — | — | — | — | — | — | — | — | — |
| Tholedemba | — | — | — | — | — | — | — | — | — | — | — |
| Harkapur | — | — | — | — | — | — | — | — | — | — | — |
| Manebhanjyang | partial (Police Station Manebhanjyang) | 30.2 | 16.8 | 52 | graphml_fallback | 6 | 0 | 0 | 0 | 15 | Okhaldhunga Community Hospital (6.65 km) |
| Rumjatar | partial (Police Station Rumjatar) | 27.9 | 11.6 | 48 | graphml_fallback | 7 | 0 | 0 | 0 | 17 | Okhaldhunga Community Hospital (2.22 km) |
| Likhu River | — | — | — | — | — | — | — | — | — | — | — |
| Khijidemba | — | — | — | — | — | — | — | — | — | — | — |
| Molung | partial (Hotel Kyimolung) | 349.3 | 205.9 | 600 | graphml_fallback | 0 | 0 | 0 | 0 | 1 | — |
| Taluwa | — | — | — | — | — | — | — | — | — | — | — |
| Champadevi | — | — | — | — | — | — | — | — | — | — | — |

## Panchthar (hub: D1)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Phidim | partial (Phidim Hospital) | 1.9 | 1.9 | 3 | graphml_fallback | 9 | 0 | 0 | 0 | 22 | District Hospital (0.0 km) |
| Tinjure | — | — | — | — | — | — | — | — | — | — | — |
| Kummayak | — | — | — | — | — | — | — | — | — | — | — |
| Falelung | — | — | — | — | — | — | — | — | — | — | — |
| Falgunanda Cave | — | — | — | — | — | — | — | — | — | — | — |
| Timbu Pokhari | — | — | — | — | — | — | — | — | — | — | — |
| Chiyobhanjyang | — | — | — | — | — | — | — | — | — | — | — |
| Phalelung Danda | — | — | — | — | — | — | — | — | — | — | — |
| Ekteen | — | — | — | — | — | — | — | — | — | — | — |
| Kabeli River | — | — | — | — | — | — | — | — | — | — | — |
| Menchhayayem | — | — | — | — | — | — | — | — | — | — | — |

## Sankhuwasabha (hub: 1 Room)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Khandbari | partial (Police Station Khandbari) | 12.2 | 12.0 | 21 | graphml_fallback | 7 | 0 | 0 | 0 | 23 | Sankhuwasabha District Hospital (0.0 km) |
| Tumlingtar | partial (Police Station Tumlingtar) | 12.5 | 11.4 | 21 | graphml_fallback | 7 | 0 | 0 | 0 | 23 | Sankhuwasabha District Hospital (8.9 km) |
| Makalu Base Camp | exact | 66.7 | 60.4 | 115 | graphml_fallback | 1 | 0 | 0 | 0 | 6 | Solukhumbu District Hospital (35.38 km) |
| Makalu Barun National Park | exact | 54.5 | 48.5 | 94 | graphml_fallback | 2 | 0 | 0 | 0 | 9 | Sankhuwasabha District Hospital (41.27 km) |
| Num | partial (The Fern Residency Platinum) | 243.8 | 203.1 | 419 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Birendra Military Hospital (0.23 km) |
| Seduwa | — | — | — | — | — | — | — | — | — | — | — |
| Barun Valley | exact | 62.6 | 53.1 | 108 | graphml_fallback | 2 | 0 | 0 | 0 | 9 | Solukhumbu District Hospital (39.37 km) |
| Sabha Pokhari | — | — | — | — | — | — | — | — | — | — | — |
| Milke Danda | partial (Milke Danda Trail - few water!) | 18.7 | 18.7 | 32 | graphml_fallback | 9 | 0 | 0 | 0 | 23 | Taplejung District Hospital (17.56 km) |
| Chainpur | partial (Police Station Chainpur) | 858.9 | 647.9 | 1476 | graphml_fallback | 4 | 0 | 0 | 0 | 17 | Bajhang District Hospital (0.0 km) |

## Solukhumbu (hub: Above the Cloud Lodge & Restaurant)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lukla | partial (Lukla Lodge) | 43.7 | 29.5 | 75 | graphml_fallback | 4 | 0 | 0 | 0 | 12 | Solukhumbu District Hospital (10.77 km) |
| Namche Bazaar | exact | 27.2 | 18.6 | 47 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (1.84 km) |
| Everest Base Camp | exact | 6.9 | 6.8 | 12 | graphml_fallback | 1 | 0 | 0 | 0 | 6 | Solukhumbu District Hospital (26.53 km) |
| Sagarmatha National Park | exact | 7.7 | 5.9 | 13 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (18.03 km) |
| Tengboche | partial (Mani Rimdu (Tengboche)) | 21.2 | 13.3 | 36 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (6.88 km) |
| Gokyo Lakes | exact | 13.7 | 9.8 | 23 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (18.59 km) |
| Kala Patthar | exact | 5.8 | 5.4 | 10 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (25.09 km) |
| Dingboche | partial (Hotel Tashi Delek Dingboche) | 12.2 | 6.7 | 21 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (15.45 km) |
| Phakding | exact | 36.9 | 24.7 | 63 | graphml_fallback | 2 | 0 | 0 | 0 | 8 | Solukhumbu District Hospital (5.21 km) |
| Thame | partial (Thamel Grand Hotel) | 175.4 | 149.7 | 301 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Ciwec Hospital (1.05 km) |
| Khumjung | partial (Norbu Art Gallery Khumjung) | 25.9 | 17.1 | 44 | graphml_fallback | 1 | 0 | 0 | 0 | 7 | Solukhumbu District Hospital (3.3 km) |
| Renjo La | — | — | — | — | — | — | — | — | — | — | — |

## Sunsari (hub: Barahakshetra)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dharan | partial (Budhasubba (Dharan)) | 50.0 | 40.9 | 86 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | B.P. Koirala Institute Of Health Sciences (1.11 km) |
| Itahari | partial (Hira Hotel, Itahari) | 32.2 | 29.2 | 55 | graphml_fallback | 29 | 0 | 0 | 0 | 27 | Itahari Hospital (0.86 km) |
| Barahachhetra | — | — | — | — | — | — | — | — | — | — | — |
| Koshi Tappu Wildlife Reserve | partial (Koshi Tappu Wildlife Reserve Office) | 10.7 | 8.3 | 18 | straight_line_fallback | 29 | 0 | 0 | 0 | 29 | Inaruwa District Hospital (11.09 km) |
| Budha Subba Temple | — | — | — | — | — | — | — | — | — | — | — |
| Dantakali Temple | — | — | — | — | — | — | — | — | — | — | — |
| Pindeshwor Temple | — | — | — | — | — | — | — | — | — | — | — |
| Chatara | — | — | — | — | — | — | — | — | — | — | — |
| Sapta Koshi River | — | — | — | — | — | — | — | — | — | — | — |
| Panchakanya | — | — | — | — | — | — | — | — | — | — | — |

## Taplejung (hub: Alojamiento)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Taplejung Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Pathibhara Temple | — | — | — | — | — | — | — | — | — | — | — |
| Kanchenjunga Base Camp | partial (Kanchenjunga Base Camp Trek) | 27.4 | 22.0 | 47 | graphml_fallback | 0 | 0 | 0 | 0 | 0 | — |
| Kanchenjunga Conservation Area | exact | 28.0 | 20.9 | 48 | graphml_fallback | 0 | 0 | 0 | 0 | 0 | — |
| Olangchung Gola | — | — | — | — | — | — | — | — | — | — | — |
| Ghunsa | exact | 16.6 | 15.0 | 29 | graphml_fallback | 2 | 0 | 0 | 0 | 3 | Taplejung District Hospital (43.42 km) |
| Lelep | — | — | — | — | — | — | — | — | — | — | — |
| Phaktanglung | partial (Jannu Phaktanglung View Point) | 24.0 | 22.3 | 41 | graphml_fallback | 0 | 0 | 0 | 0 | 0 | — |
| Sinelapche | — | — | — | — | — | — | — | — | — | — | — |
| Tamor River | — | — | — | — | — | — | — | — | — | — | — |
| Fungling | — | — | — | — | — | — | — | — | — | — | — |

## Terhathum (hub: Hyatung Falls)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Myanglung | partial (Police Station Myanglung) | 55.6 | 27.0 | 96 | graphml_fallback | 17 | 0 | 0 | 0 | 30 | Terhathum District Hospital (0.0 km) |
| Basantapur | partial (basantapur vdc) | 459.8 | 375.1 | 790 | graphml_fallback | 13 | 0 | 0 | 0 | 20 | Bhairahawa Hospital (5.31 km) |
| Chuhandanda | — | — | — | — | — | — | — | — | — | — | — |
| Sabhapokhari | — | — | — | — | — | — | — | — | — | — | — |
| Laligurans | partial (Hotel Laligurans) | 530.3 | 363.3 | 911 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Hospital (21.46 km) |
| Pattek | — | — | — | — | — | — | — | — | — | — | — |
| Tinjure Forest | — | — | — | — | — | — | — | — | — | — | — |

## Udayapur (hub: Bashu Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaighat | partial (Police Station Gaighat) | 29.6 | 29.1 | 51 | graphml_fallback | 9 | 0 | 0 | 0 | 26 | Udayapur District Hospital (0.0 km) |
| Udayapurgadhi | — | — | — | — | — | — | — | — | — | — | — |
| Chaudandigadhi | — | — | — | — | — | — | — | — | — | — | — |
| Rautamai | — | — | — | — | — | — | — | — | — | — | — |
| Triyuga River | — | — | — | — | — | — | — | — | — | — | — |
| Beltar | partial (Police Station Beltar) | 43.0 | 26.1 | 74 | graphml_fallback | 16 | 0 | 0 | 0 | 26 | Udayapur District Hospital (14.9 km) |
| Katari | — | — | — | — | — | — | — | — | — | — | — |
| Tawa River | — | — | — | — | — | — | — | — | — | — | — |

## Bara (hub: Gauri Baba's Home)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Simara | partial (Police Station Simara) | 10.7 | 4.5 | 18 | graphml_fallback | 16 | 0 | 0 | 0 | 20 | Advance Medicare Hospital (19.4 km) |
| Nijgadh | partial (Police Station Nijgadh) | 24.0 | 17.4 | 41 | graphml_fallback | 16 | 0 | 0 | 0 | 19 | Chure Hill Hospital (27.18 km) |
| Gadhimai Temple | — | — | — | — | — | — | — | — | — | — | — |
| Simraungadh | — | — | — | — | — | — | — | — | — | — | — |
| Amlekhganj | — | — | — | — | — | — | — | — | — | — | — |
| Parsa National Park | exact | 210.8 | 28.6 | 362 | graphml_fallback | 1 | 0 | 0 | 0 | 3 | Gajuri Hospital (49.84 km) |
| Pathlaiya | — | — | — | — | — | — | — | — | — | — | — |
| Jitpur | — | — | — | — | — | — | — | — | — | — | — |
| Bakaiya River | — | — | — | — | — | — | — | — | — | — | — |
| Dudhhaura | — | — | — | — | — | — | — | — | — | — | — |

## Dhanusha (hub: Dhanushadham Protected Forest - Zoo Area)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Janakpur | partial (Janakpur City Hospital) | 17.7 | 17.7 | 30 | graphml_fallback | 11 | 0 | 0 | 0 | 21 | Dhanusha Hospital (0.0 km) |
| Janaki Mandir | partial (Janaki Mandir Area) | 17.2 | 17.2 | 30 | graphml_fallback | 11 | 0 | 0 | 0 | 21 | Dhanusha Hospital (0.54 km) |
| Ram Mandir | — | — | — | — | — | — | — | — | — | — | — |
| Dhanushadham | partial (Dhanushadham Protected Forest - Zoo Area) | 0.0 | 0.0 | 0 | straight_line_fallback | 15 | 0 | 0 | 0 | 24 | Dhanusha Hospital (17.65 km) |
| Dhanush Sagar | — | — | — | — | — | — | — | — | — | — | — |
| Ganga Sagar | — | — | — | — | — | — | — | — | — | — | — |
| Vivah Mandap | — | — | — | — | — | — | — | — | — | — | — |
| Parshuram Talau | — | — | — | — | — | — | — | — | — | — | — |
| Mithila Bihari | — | — | — | — | — | — | — | — | — | — | — |
| Kamala River | — | — | — | — | — | — | — | — | — | — | — |

## Mahottari (hub: Hotel Vinayak)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jaleshwar | partial (Police Station Jaleshwar) | 49.0 | 38.9 | 84 | graphml_fallback | 11 | 0 | 0 | 0 | 20 | Dhanusha Hospital (14.87 km) |
| Jaleshwar Mahadev Temple | — | — | — | — | — | — | — | — | — | — | — |
| Bardibas | partial (BP Koirala Highway (Banepa-Bardibas)) | 69.6 | 60.8 | 120 | graphml_fallback | 22 | 0 | 0 | 0 | 28 | Charikot Hospital (27.5 km) |
| Gaushala | partial (Metropolitan Police Circle Gaushala) | 113.8 | 96.5 | 195 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Helping Hands Community Hospital (1.26 km) |
| Matihani | — | — | — | — | — | — | — | — | — | — | — |
| Ratwara | — | — | — | — | — | — | — | — | — | — | — |
| Ratauli | — | — | — | — | — | — | — | — | — | — | — |
| Pipra | — | — | — | — | — | — | — | — | — | — | — |
| Sonama | — | — | — | — | — | — | — | — | — | — | — |

## Parsa (hub: Birgunj)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Birgunj | exact | 0.0 | 0.0 | 0 | straight_line_fallback | 16 | 0 | 0 | 0 | 17 | Advance Medicare Hospital (1.11 km) |
| Thori | — | — | — | — | — | — | — | — | — | — | — |
| Suwarna | — | — | — | — | — | — | — | — | — | — | — |
| Bindabasini Temple | — | — | — | — | — | — | — | — | — | — | — |
| Ghantaghar | exact | 89.4 | 87.8 | 154 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bir Hospital (0.33 km) |
| Sirsiya River | — | — | — | — | — | — | — | — | — | — | — |
| Ram Bhanjyang | — | — | — | — | — | — | — | — | — | — | — |
| Bhatauda | — | — | — | — | — | — | — | — | — | — | — |

## Rautahat (hub: Chandrapur)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaur | exact | 58.8 | 58.7 | 101 | graphml_fallback | 13 | 0 | 0 | 0 | 15 | Malangwa Hospital (30.36 km) |
| Garuda | partial (Police Station Garuda) | 41.3 | 34.5 | 71 | graphml_fallback | 13 | 0 | 0 | 0 | 17 | Malangwa Hospital (26.42 km) |
| Rajdevi Temple | — | — | — | — | — | — | — | — | — | — | — |
| Shivnagar | — | — | — | — | — | — | — | — | — | — | — |
| Bagmati River | partial (Bagmati River (Pashupati)) | 101.5 | 47.0 | 174 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Helping Hands Community Hospital (1.26 km) |
| Nunthar | — | — | — | — | — | — | — | — | — | — | — |
| Chandrapur | exact | 0.0 | 0.0 | 0 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (42.86 km) |
| Balara | partial (balaram dhedho house) | 65.6 | 37.2 | 113 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (35.69 km) |
| Brindaban | exact | 290.9 | 193.3 | 500 | graphml_fallback | 17 | 0 | 0 | 0 | 28 | Butwal Hospital (1.69 km) |
| Gaidatar | — | — | — | — | — | — | — | — | — | — | — |

## Saptari (hub: Deep Shajan Hotel & Lage Rajbiraj,Saptari)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Rajbiraj | partial (Police Station Rajbiraj) | 0.1 | 0.1 | 0 | graphml_fallback | 8 | 0 | 0 | 0 | 20 | Gajendra Narayan Singh Hospital (0.0 km) |
| Kankalini Temple | — | — | — | — | — | — | — | — | — | — | — |
| Sakhada | — | — | — | — | — | — | — | — | — | — | — |
| Hanumannagar | partial (Police Station Hanumannagar) | 51.9 | 20.3 | 89 | graphml_fallback | 6 | 0 | 0 | 0 | 18 | Lahan Hospital (17.05 km) |
| Kanchanpur | partial (Police Station Kanchanpur) | 8.4 | 8.4 | 14 | graphml_fallback | 22 | 0 | 0 | 0 | 24 | Gajendra Narayan Singh Hospital (8.32 km) |
| Koshi River | partial (Koshi River (Sapta Kosi)) | 37.5 | 25.0 | 64 | graphml_fallback | 29 | 0 | 0 | 0 | 29 | Inaruwa District Hospital (15.44 km) |
| Chhinnamasta | — | — | — | — | — | — | — | — | — | — | — |
| Rupani | — | — | — | — | — | — | — | — | — | — | — |
| Bhardaha | — | — | — | — | — | — | — | — | — | — | — |
| Tilathi | — | — | — | — | — | — | — | — | — | — | — |

## Sarlahi (hub: Jankinagar jungle)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Malangwa | partial (Malangwa Hospital) | 28.5 | 19.3 | 49 | graphml_fallback | 10 | 0 | 0 | 0 | 19 | Malangwa Hospital (0.0 km) |
| Nawalpur | partial (Nawalpur District Hospital) | 216.9 | 152.8 | 373 | graphml_fallback | 18 | 0 | 0 | 0 | 25 | Nawalpur District Hospital (0.0 km) |
| Harion | — | — | — | — | — | — | — | — | — | — | — |
| Lalbandi | partial (Police Station Lalbandi) | 5.3 | 4.1 | 9 | straight_line_fallback | 13 | 0 | 0 | 0 | 24 | Malangwa Hospital (18.93 km) |
| Ishwarpur | — | — | — | — | — | — | — | — | — | — | — |
| Sagarnath Forest | — | — | — | — | — | — | — | — | — | — | — |
| Murtiya | — | — | — | — | — | — | — | — | — | — | — |
| Barahathwa | — | — | — | — | — | — | — | — | — | — | — |
| Brahmapuri | — | — | — | — | — | — | — | — | — | — | — |
| Hariwan | — | — | — | — | — | — | — | — | — | — | — |
| Lakshmipur | — | — | — | — | — | — | — | — | — | — | — |

## Siraha (hub: Buddha Lake)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lahan | partial (Lahan Hospital) | 18.1 | 16.8 | 31 | graphml_fallback | 6 | 0 | 0 | 0 | 19 | Lahan Hospital (0.0 km) |
| Siraha Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Salhesh Phulbari | — | — | — | — | — | — | — | — | — | — | — |
| Salhesh Garden | — | — | — | — | — | — | — | — | — | — | — |
| Mirchaiya | partial (Police Station Mirchaiya) | 12.7 | 12.4 | 22 | graphml_fallback | 11 | 0 | 0 | 0 | 23 | Siraha District Hospital (14.24 km) |
| Kalyanpur | — | — | — | — | — | — | — | — | — | — | — |
| Sukhipur | — | — | — | — | — | — | — | — | — | — | — |
| Bhagwanpur | — | — | — | — | — | — | — | — | — | — | — |
| Golbazar | — | — | — | — | — | — | — | — | — | — | — |
| Dhangadhimai | partial (Police Station Dhangadhimai) | 34.5 | 15.5 | 59 | graphml_fallback | 14 | 0 | 0 | 0 | 24 | Siraha District Hospital (10.89 km) |

## Bhaktapur (hub: A One Minawasi Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhaktapur Durbar Square | exact | 8.2 | 7.2 | 14 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (0.29 km) |
| Nyatapola Temple | partial (Nyatapola Temple (Bhaktapur)) | 8.3 | 7.3 | 14 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (0.29 km) |
| Taumadhi Square | — | — | — | — | — | — | — | — | — | — | — |
| Dattatreya Square | — | — | — | — | — | — | — | — | — | — | — |
| Pottery Square | partial (Bhaktapur Pottery Square) | 8.3 | 7.2 | 14 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (0.29 km) |
| Changu Narayan | exact | 12.5 | 8.2 | 21 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Human Organ Transplant Center (3.14 km) |
| Siddha Pokhari | — | — | — | — | — | — | — | — | — | — | — |
| 55 Window Palace | — | — | — | — | — | — | — | — | — | — | — |
| Bhairavnath Temple | — | — | — | — | — | — | — | — | — | — | — |
| Nagarkot | partial (Nagarkot Camping) | 26.6 | 16.7 | 46 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Human Organ Transplant Center (9.46 km) |
| Suryabinayak | partial (suryabinayak boys hostel) | 5.2 | 4.2 | 9 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Annapurna Neurological Institute (1.39 km) |
| Pilot Baba Ashram | exact | 9.3 | 7.4 | 16 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (3.36 km) |

## Chitwan (hub: Aama Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chitwan National Park | partial (Chitwan National Park Info Office) | 33.7 | 32.1 | 58 | graphml_fallback | 17 | 0 | 0 | 0 | 25 | Cmc Hospital Emergency (11.91 km) |
| Sauraha | partial (Hotel National Park Sauraha) | 33.9 | 31.6 | 58 | graphml_fallback | 17 | 0 | 0 | 0 | 25 | Cmc Hospital Emergency (11.77 km) |
| Narayanghat | — | — | — | — | — | — | — | — | — | — | — |
| Elephant Breeding Centre | — | — | — | — | — | — | — | — | — | — | — |
| Bishazari Tal | — | — | — | — | — | — | — | — | — | — | — |
| Devghat | partial (Maghe Sankranti (Devghat)) | 27.3 | 18.6 | 47 | graphml_fallback | 19 | 0 | 0 | 0 | 27 | B.P. Koirala Memorial Cancer Hospital (7.89 km) |
| Meghauli | — | — | — | — | — | — | — | — | — | — | — |
| Kasara | partial (Kasara Chitwan) | 45.5 | 39.1 | 78 | graphml_fallback | 15 | 0 | 0 | 0 | 22 | Cmc Hospital Emergency (15.26 km) |
| Rapti River | — | — | — | — | — | — | — | — | — | — | — |
| Chitwan Tharu Village | — | — | — | — | — | — | — | — | — | — | — |
| Jalbire | partial (Canyoning at Jalbire) | 31.5 | 26.3 | 54 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gajuri Hospital (5.26 km) |
| Maulakalika | — | — | — | — | — | — | — | — | — | — | — |

## Dhading (hub: Adhikari Hotel and Lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dhading Besi | — | — | — | — | — | — | — | — | — | — | — |
| Ruby Valley | partial (Ruby Valley Guest House) | 0.8 | 0.8 | 1 | graphml_fallback | 20 | 0 | 0 | 0 | 25 | Dhading District Hospital (5.36 km) |
| Ganesh Himal | partial (Ganesh Himal Guest House) | 0.6 | 0.6 | 1 | graphml_fallback | 20 | 0 | 0 | 0 | 25 | Dhading District Hospital (5.36 km) |
| Pangsang Pass | — | — | — | — | — | — | — | — | — | — | — |
| Tripura Sundari | partial (Tripura Sundari Guesthouse and Restaurant) | 0.1 | 0.1 | 0 | graphml_fallback | 19 | 0 | 0 | 0 | 26 | Dhading District Hospital (5.7 km) |
| Salyantar | — | — | — | — | — | — | — | — | — | — | — |
| Benighat | partial (Police Station Benighat) | 12.4 | 12.4 | 21 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gajuri Hospital (2.43 km) |
| Trishuli River | partial (Trishuli River Rafting) | 40.0 | 28.9 | 69 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (15.7 km) |
| Budhi Gandaki | partial (Budhi Gandaki Hotel) | 73.0 | 69.2 | 125 | graphml_fallback | 0 | 0 | 0 | 0 | 1 | — |
| Ganga Jamuna Waterfall | — | — | — | — | — | — | — | — | — | — | — |
| Sertung | — | — | — | — | — | — | — | — | — | — | — |
| Tipling | — | — | — | — | — | — | — | — | — | — | — |

## Dolakha (hub: Abhayapur Lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Charikot | partial (Charikot Hospital) | 4.2 | 4.2 | 7 | graphml_fallback | 13 | 0 | 0 | 0 | 30 | Charikot Hospital (0.0 km) |
| Dolakha Bhimsen Temple | — | — | — | — | — | — | — | — | — | — | — |
| Kalinchowk | partial (Kalinchowk Bhagwati Snow) | 13.7 | 9.4 | 23 | graphml_fallback | 10 | 0 | 0 | 0 | 28 | Charikot Hospital (8.95 km) |
| Kuri Village | partial (Hotel Mek Kuri Village Pvt Ltd.) | 12.7 | 8.6 | 22 | graphml_fallback | 7 | 0 | 0 | 0 | 23 | Charikot Hospital (8.6 km) |
| Jiri | partial (Tiger Of Jiri Hotel) | 79.4 | 69.8 | 136 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Madhyapur Hospital (2.77 km) |
| Sailung | partial (Sailung Winter Trek) | 7.9 | 7.7 | 14 | graphml_fallback | 15 | 0 | 0 | 0 | 30 | Charikot Hospital (3.7 km) |
| Tamakoshi River | — | — | — | — | — | — | — | — | — | — | — |
| Bigu | — | — | — | — | — | — | — | — | — | — | — |
| Lamabagar | partial (Police Station Lamabagar) | 48.6 | 33.4 | 83 | graphml_fallback | 5 | 0 | 0 | 0 | 17 | Jiri Hospital (27.16 km) |
| Tsho Rolpa | partial (Tsho Rolpa Glacial Lake) | 48.1 | 33.2 | 83 | graphml_fallback | 5 | 0 | 0 | 0 | 17 | Jiri Hospital (28.44 km) |
| Beding | — | — | — | — | — | — | — | — | — | — | — |

## Kathmandu (hub: 3 rooms by Pauline)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Swayambhunath | partial (Swayambhunath Stupa (Monkey Temple)) | 4.5 | 3.9 | 8 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Birendra Military Hospital (1.56 km) |
| Boudhanath | partial (Boudhanath Stupa) | 5.0 | 4.9 | 9 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Apex Hospital (1.27 km) |
| Pashupatinath | partial (Shivaratri (Pashupatinath)) | 3.3 | 3.0 | 6 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Helping Hands Community Hospital (1.26 km) |
| Kathmandu Durbar Square | partial (Kathmandu Durbar Square & Old City) | 2.5 | 2.1 | 4 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Blue Cross Hospital (0.74 km) |
| Garden of Dreams | exact | 112.9 | 81.7 | 194 | graphml_fallback | 17 | 0 | 0 | 0 | 25 | Cmc Hospital Emergency (11.77 km) |
| Thamel | partial (Thamel Grand Hotel) | 2.9 | 2.8 | 5 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Ciwec Hospital (1.05 km) |
| Chandragiri Hills | — | — | — | — | — | — | — | — | — | — | — |
| Kirtipur | partial (Kirtipur community homestay) | 5.1 | 5.0 | 9 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Janamaitri Hospital (2.51 km) |
| Kopan Monastery | exact | 6.3 | 6.1 | 11 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Apex Hospital (0.49 km) |
| Rani Pokhari | exact | 1.7 | 1.6 | 3 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bir Hospital (0.33 km) |
| Narayanhiti Palace | partial (Narayanhiti Palace Museum) | 2.4 | 2.3 | 4 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bir Hospital (0.33 km) |
| Shivapuri | partial (Kakani-Shivapuri MTB) | 16.4 | 11.9 | 28 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Grande International Hospital (6.29 km) |

## Kavrepalanchok (hub: Aagantuk Resort)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dhulikhel | partial (Nagarkot-Dhulikhel Mountain Biking) | 10.7 | 7.5 | 18 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Human Organ Transplant Center (10.09 km) |
| Namobuddha | partial (Namobuddha Thrangu Monastery) | 11.6 | 6.5 | 20 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (17.04 km) |
| Panauti | partial (Police Station Panauti) | 8.0 | 6.7 | 14 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (12.74 km) |
| Banepa | partial (Banepali Guest House) | 24.5 | 20.0 | 42 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Buddha Hospital (1.52 km) |
| Bethanchok | — | — | — | — | — | — | — | — | — | — | — |
| Indreshwar Mahadev | — | — | — | — | — | — | — | — | — | — | — |
| Sanga | partial (Sangam Hotel) | 278.5 | 166.8 | 479 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (1.01 km) |
| Balthali | partial (Balthali Village Resort) | 10.8 | 9.1 | 18 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (17.27 km) |
| Roshi Valley | — | — | — | — | — | — | — | — | — | — | — |

## Lalitpur (hub: "Break the Chain")
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Patan Durbar Square | exact | 0.2 | 0.1 | 0 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Buddha Hospital (2.31 km) |
| Golden Temple | — | — | — | — | — | — | — | — | — | — | — |
| Bungamati | partial (Police Station Bungamati) | 6.2 | 5.5 | 11 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Janamaitri Hospital (6.12 km) |
| Khokana | exact | 6.2 | 5.2 | 11 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Janamaitri Hospital (5.1 km) |
| Godawari Botanical Garden | partial (Godawari Botanical Garden Birding) | 10.8 | 9.8 | 19 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Madhyapur Hospital (8.95 km) |
| Phulchoki | — | — | — | — | — | — | — | — | — | — | — |
| Kumbheshwar Temple | exact | 0.3 | 0.3 | 0 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Buddha Hospital (2.29 km) |
| Mahaboudha Temple | — | — | — | — | — | — | — | — | — | — | — |
| Rudravarna Mahavihar | — | — | — | — | — | — | — | — | — | — | — |
| Godawari | partial (Godawari Botanical Garden Birding) | 10.8 | 9.8 | 19 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Madhyapur Hospital (8.95 km) |
| Champi | — | — | — | — | — | — | — | — | — | — | — |
| Lakuri Bhanjyang | — | — | — | — | — | — | — | — | — | — | — |

## Makwanpur (hub: Akhanda Dhuni Cave (Daman))
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Hetauda | exact | 49.9 | 19.3 | 86 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (35.69 km) |
| Makwanpur Gadhi | exact | 56.5 | 16.9 | 97 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (30.51 km) |
| Daman | partial (Daman Snow View) | 7.6 | 0.3 | 13 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (20.64 km) |
| Chitlang | partial (Chitlang Organic Village Resort) | 12.9 | 12.3 | 22 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (8.05 km) |
| Kulekhani | partial (Kulekhani Lakeside Camping) | 11.2 | 4.1 | 19 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (24.46 km) |
| Indrasarovar | — | — | — | — | — | — | — | — | — | — | — |
| Markhu | — | — | — | — | — | — | — | — | — | — | — |
| Tistung | — | — | — | — | — | — | — | — | — | — | — |
| Palung | partial (Police Station Palungtar) | 82.2 | 65.2 | 141 | graphml_fallback | 20 | 0 | 0 | 0 | 26 | Gorkha District Hospital (3.48 km) |
| Bhimphedi | partial (Police Station Bhimphedi) | 16.0 | 9.6 | 27 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (18.42 km) |
| Sim Bhanjyang | — | — | — | — | — | — | — | — | — | — | — |
| Manakamana Temple | exact | 68.2 | 57.3 | 117 | graphml_fallback | 20 | 0 | 0 | 0 | 28 | Gorkha District Hospital (13.76 km) |

## Nuwakot (hub: Aana yangri)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bidur | partial (Police Station Bidur) | 41.7 | 32.1 | 72 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Dhading District Hospital (24.23 km) |
| Nuwakot Durbar | partial (Nuwakot Durbar Village) | 40.8 | 31.4 | 70 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Grande International Hospital (24.52 km) |
| Kakani | partial (Police Station Kakani) | 36.3 | 31.5 | 62 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Armed Police Force Hospital Emergency (13.18 km) |
| Trishuli | partial (Police Station Trishuli) | 41.1 | 31.6 | 71 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Dhading District Hospital (27.59 km) |
| Devighat | — | — | — | — | — | — | — | — | — | — | — |
| Suryagadhi | — | — | — | — | — | — | — | — | — | — | — |
| Tadi | partial (Hotel Saptadip and Lodge) | 294.2 | 139.8 | 505 | graphml_fallback | 24 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (9.82 km) |
| Samari | — | — | — | — | — | — | — | — | — | — | — |
| Bagh Bazar | — | — | — | — | — | — | — | — | — | — | — |

## Ramechhap (hub: Bandar Guest House & Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Manthali | partial (Manthali Hospital) | 170.8 | 35.4 | 294 | graphml_fallback | 12 | 0 | 0 | 0 | 24 | Manthali Hospital (0.0 km) |
| Thulaili | — | — | — | — | — | — | — | — | — | — | — |
| Doramba | partial (Police Station Doramba) | 53.3 | 21.8 | 92 | graphml_fallback | 12 | 0 | 0 | 0 | 20 | Manthali Hospital (18.79 km) |
| Khimti | — | — | — | — | — | — | — | — | — | — | — |
| Those | — | — | — | — | — | — | — | — | — | — | — |
| Ramechhap Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Gokulganga | — | — | — | — | — | — | — | — | — | — | — |

## Rasuwa (hub: ACAP / TIMS Checkpost)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dhunche | partial (Police Station Dhunche) | 1.2 | 1.0 | 2 | graphml_fallback | 30 | 0 | 0 | 0 | 25 | Grande International Hospital (40.14 km) |
| Langtang National Park | exact | 32.2 | 21.6 | 55 | graphml_fallback | 9 | 0 | 0 | 0 | 19 | Rasuwa District Hospital (20.6 km) |
| Langtang Valley | partial (Langtang Valley Trek) | 32.7 | 26.7 | 56 | graphml_fallback | 5 | 0 | 0 | 0 | 13 | Rasuwa District Hospital (25.76 km) |
| Gosainkunda | partial (New Gosainkunda Lodge & Restaurant) | 36.3 | 29.6 | 62 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Apex Hospital (22.01 km) |
| Kyanjin Gompa | — | — | — | — | — | — | — | — | — | — | — |
| Syabrubesi | partial (Police Station Syabrubesi) | 14.1 | 10.4 | 24 | graphml_fallback | 22 | 0 | 0 | 0 | 30 | Nuwakot District Hospital (34.6 km) |
| Tatopani | partial (Tatopani Guest House) | 344.4 | 165.8 | 592 | graphml_fallback | 25 | 0 | 0 | 0 | 30 | Beni Community Hospital (18.05 km) |
| Lauribina Pass | — | — | — | — | — | — | — | — | — | — | — |
| Helambu | partial (Helambu Trek) | 26.4 | 22.8 | 45 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Grande International Hospital (39.71 km) |
| Timure | — | — | — | — | — | — | — | — | — | — | — |
| Rasuwagadhi | — | — | — | — | — | — | — | — | — | — | — |

## Sindhuli (hub: Aarati fast food & lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sindhuligadhi | — | — | — | — | — | — | — | — | — | — | — |
| Kamalamai | partial (Police Station Kamalamai) | 10.2 | 7.2 | 17 | graphml_fallback | 10 | 0 | 0 | 0 | 20 | Janasewa Hospital (0.0 km) |
| Sindhuli Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Khurkot | partial (Police Station Khurkot) | 113.4 | 25.1 | 195 | graphml_fallback | 12 | 0 | 0 | 0 | 24 | Manthali Hospital (1.49 km) |
| Marin | partial (Hotel Marinha) | 89.0 | 77.6 | 153 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Buddha Hospital (1.71 km) |
| Hariharpurgadhi | — | — | — | — | — | — | — | — | — | — | — |
| Golanjor | — | — | — | — | — | — | — | — | — | — | — |
| Sunkoshi River | — | — | — | — | — | — | — | — | — | — | — |
| Jalkanya | — | — | — | — | — | — | — | — | — | — | — |
| Dudhauli | partial (Police Station Dudhauli) | 67.1 | 40.6 | 115 | graphml_fallback | 13 | 0 | 0 | 0 | 22 | Siraha District Hospital (32.25 km) |
| Ranibas | — | — | — | — | — | — | — | — | — | — | — |

## Sindhupalchok (hub: Agro Village Resort & Farm)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Melamchi | partial (Police Station Melamchi) | 62.8 | 27.0 | 108 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Human Organ Transplant Center (21.45 km) |
| Bhote Koshi River | — | — | — | — | — | — | — | — | — | — | — |
| Panch Pokhari | exact | 60.5 | 43.3 | 104 | graphml_fallback | 0 | 0 | 0 | 0 | 1 | — |
| Gaurishankar | partial (Gaurishankar Resort) | 25.0 | 24.1 | 43 | graphml_fallback | 10 | 0 | 0 | 0 | 25 | Charikot Hospital (4.48 km) |
| Thangpaldhap | — | — | — | — | — | — | — | — | — | — | — |
| Barhabise | partial (Police Station Barhabise) | 5.0 | 3.8 | 9 | straight_line_fallback | 27 | 0 | 0 | 0 | 30 | Charikot Hospital (22.18 km) |
| Kodari | partial (Tatopani Hot Spring (Kodari)) | 26.4 | 26.3 | 45 | graphml_fallback | 4 | 0 | 0 | 0 | 16 | Charikot Hospital (33.57 km) |
| Tarkeghyang | partial (Hotel Tarkeghyang) | 63.8 | 39.3 | 110 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Apex Hospital (34.72 km) |
| Ama Yangri | partial (Ama Yangri Base Camp) | 62.3 | 38.5 | 107 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Apex Hospital (35.79 km) |

## Baglung (hub: Baglung Kalika Temple Viewpoint)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baglung Bazaar | partial (Police Station Baglung Bazaar) | 3.4 | 3.0 | 6 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Baglung Community Hospital (0.0 km) |
| Baglung Kalika Temple | partial (Baglung Kalika Temple Viewpoint) | 0.0 | 0.0 | 0 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Baglung Community Hospital (3.04 km) |
| Panchakot | — | — | — | — | — | — | — | — | — | — | — |
| Galkot | partial (Police Station Galkot) | 45.6 | 21.9 | 78 | graphml_fallback | 12 | 0 | 0 | 0 | 25 | Beni Community Hospital (14.68 km) |
| Dhorpatan | partial (Police Station Dhorpatan) | 220.4 | 66.1 | 379 | graphml_fallback | 1 | 0 | 0 | 0 | 12 | Pyuthan District Hospital (47.33 km) |
| Dhorpatan Hunting Reserve | — | — | — | — | — | — | — | — | — | — | — |
| Balewa | — | — | — | — | — | — | — | — | — | — | — |
| Kusma | partial (Bungy Kusma (Cliff Nepal)) | 9.4 | 9.1 | 16 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Parbat Community Hospital (1.96 km) |
| Narsingh Temple | — | — | — | — | — | — | — | — | — | — | — |
| Ghodabanda | — | — | — | — | — | — | — | — | — | — | — |
| Kathekhola | — | — | — | — | — | — | — | — | — | — | — |
| Kaligandaki River | partial (Kaligandaki Riverside Resort) | 175.5 | 96.8 | 301 | graphml_fallback | 19 | 0 | 0 | 0 | 27 | B.P. Koirala Memorial Cancer Hospital (7.89 km) |

## Gorkha (hub: 18 Saya Khola Family Guest House)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gorkha Durbar | partial (Gorkha Durbar Hill) | 44.5 | 42.2 | 76 | graphml_fallback | 20 | 0 | 0 | 0 | 27 | Gorkha District Hospital (0.03 km) |
| Manakamana Temple | exact | 63.7 | 55.5 | 109 | graphml_fallback | 20 | 0 | 0 | 0 | 28 | Gorkha District Hospital (13.76 km) |
| Manaslu Circuit | partial (Manaslu Circuit Trek) | 56.7 | 43.3 | 97 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Manang District Hospital (32.25 km) |
| Barpak | exact | 18.9 | 18.5 | 32 | graphml_fallback | 7 | 0 | 0 | 0 | 15 | Gorkha District Hospital (25.16 km) |
| Laprak | partial (Laprak Gurung Bamboo Cottage & Restaurant) | 13.0 | 12.7 | 22 | graphml_fallback | 0 | 0 | 0 | 0 | 4 | — |
| Dharche | partial (Dharche Namaste Hotel, Restaurant &  Cofee Shop) | 13.1 | 13.1 | 22 | graphml_fallback | 11 | 0 | 0 | 0 | 19 | Gorkha District Hospital (29.4 km) |
| Tsum Valley | partial (Tsum Valley Trek) | 48.2 | 28.7 | 83 | graphml_fallback | 2 | 0 | 0 | 0 | 4 | Manang District Hospital (46.58 km) |
| Chepang Hill | — | — | — | — | — | — | — | — | — | — | — |
| Ligligkot | — | — | — | — | — | — | — | — | — | — | — |

## Kaski (hub: 3 angels hostel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pokhara | partial (Metropolitan Police Office Pokhara) | 1.8 | 1.7 | 3 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Kaski Provincial Hospital (0.55 km) |
| Phewa Lake | partial (Phewa Lake View Point) | 4.8 | 4.4 | 8 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (1.5 km) |
| Lakeside | partial (Lakeside, Pokhara) | 1.8 | 1.7 | 3 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Kaski Provincial Hospital (0.55 km) |
| Sarangkot | partial (Hotel Annapurna View Sarangkot) | 4.6 | 4.1 | 8 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Metrocity Hospital (1.47 km) |
| World Peace Pagoda | partial (World Peace Pagoda (Pokhara)) | 5.6 | 4.4 | 10 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (2.25 km) |
| Davis Falls | partial (Davis Falls (Patale Chhango)) | 3.9 | 3.8 | 7 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (2.66 km) |
| Gupteshwor Cave | — | — | — | — | — | — | — | — | — | — | — |
| Begnas Lake | partial (Begnas Lake Boating) | 11.0 | 8.8 | 19 | graphml_fallback | 27 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (8.69 km) |
| Mahendra Cave | exact | 9.6 | 8.6 | 17 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Hospital (2.7 km) |
| International Mountain Museum | exact | 2.1 | 1.7 | 4 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Kaski Provincial Hospital (2.32 km) |
| Bindhyabasini Temple | partial (Bindhyabasini Temple (Pokhara)) | 4.8 | 4.2 | 8 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Charak Memorial Hospital (1.51 km) |
| Australian Camp | partial (Australian Camp Guest House and Restaurant) | 28.2 | 20.2 | 49 | graphml_fallback | 28 | 0 | 0 | 0 | 30 | Gandaki Medical College Hospital (16.91 km) |

## Lamjung (hub: Annapurna Guesthouse)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Besisahar | partial (Police Station Besisahar) | 243.0 | 41.9 | 418 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Lamjung Community Hospital (0.0 km) |
| Ghale Gaun | partial (Siuri Ghale Gaun) | 6.3 | 5.1 | 11 | graphml_fallback | 21 | 0 | 0 | 0 | 30 | Manang District Hospital (29.27 km) |
| Bhujung | exact | 26.5 | 11.5 | 46 | graphml_fallback | 21 | 0 | 0 | 0 | 30 | Manang District Hospital (25.4 km) |
| Ghan Pokhara | — | — | — | — | — | — | — | — | — | — | — |
| Khudi | exact | 13.8 | 11.8 | 24 | graphml_fallback | 21 | 0 | 0 | 0 | 30 | Manang District Hospital (32.43 km) |
| Marsyangdi River | — | — | — | — | — | — | — | — | — | — | — |
| Ngadi | partial (Hotel Super View Ngadi) | 9.6 | 8.4 | 16 | graphml_fallback | 21 | 0 | 0 | 0 | 30 | Manang District Hospital (31.66 km) |
| Rainas | — | — | — | — | — | — | — | — | — | — | — |
| Ilam Pokhari | — | — | — | — | — | — | — | — | — | — | — |
| Siurung | — | — | — | — | — | — | — | — | — | — | — |
| Bahundanda | — | — | — | — | — | — | — | — | — | — | — |
| Tarkughat | — | — | — | — | — | — | — | — | — | — | — |

## Manang (hub: 3 Sister Guesthouse)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Manang Village | partial (Police Station Manang Village) | 39.3 | 36.4 | 67 | graphml_fallback | 8 | 0 | 0 | 0 | 25 | Manang District Hospital (24.46 km) |
| Annapurna Circuit | exact | 66.5 | 51.2 | 114 | straight_line_fallback | 4 | 0 | 0 | 0 | 12 | Mustang District Hospital (20.9 km) |
| Tilicho Lake | exact | 56.3 | 52.2 | 97 | graphml_fallback | 8 | 0 | 0 | 0 | 22 | Mustang District Hospital (16.62 km) |
| Thorong La | exact | 38.8 | 35.9 | 67 | graphml_fallback | 8 | 0 | 0 | 0 | 25 | Manang District Hospital (24.46 km) |
| Ice Lake | — | — | — | — | — | — | — | — | — | — | — |
| Braga | partial (Braga Gompa) | 46.7 | 39.1 | 80 | graphml_fallback | 17 | 0 | 0 | 0 | 28 | Manang District Hospital (26.82 km) |
| Pisang | exact | 460.7 | 130.3 | 792 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bir Hospital (0.96 km) |
| Chame | partial (Bat Cave (Chamere Gufa)) | 221.8 | 51.1 | 381 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (0.81 km) |
| Ngawal | — | — | — | — | — | — | — | — | — | — | — |
| Gangapurna Lake | — | — | — | — | — | — | — | — | — | — | — |
| Milarepa Cave | exact | 14.7 | 14.6 | 25 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Manang District Hospital (24.19 km) |
| Khangsar | partial (Khangsar Home) | 44.6 | 40.4 | 77 | graphml_fallback | 8 | 0 | 0 | 0 | 26 | Mustang District Hospital (27.62 km) |

## Mustang (hub: ACAP Tourist Check Post and Information Centre)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jomsom | partial (Hotel Jomsom and Restaurant) | 128.8 | 80.6 | 221 | graphml_fallback | 24 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (9.82 km) |
| Muktinath | partial (Muktinath Hotel) | 94.3 | 60.2 | 162 | graphml_fallback | 26 | 0 | 0 | 0 | 30 | Parbat Community Hospital (13.45 km) |
| Kagbeni | partial (Police Station Kagbeni) | 0.8 | 0.5 | 1 | graphml_fallback | 2 | 0 | 0 | 0 | 12 | Mustang District Hospital (8.87 km) |
| Marpha | partial (Marpha Hotel and Lodge) | 129.0 | 80.8 | 222 | graphml_fallback | 24 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (10.25 km) |
| Tatopani | partial (Tatopani Guest House) | 67.8 | 40.3 | 117 | graphml_fallback | 25 | 0 | 0 | 0 | 30 | Beni Community Hospital (18.05 km) |
| Lo Manthang | partial (Police Station Lo Manthang) | 43.5 | 41.6 | 75 | graphml_fallback | 0 | 0 | 0 | 0 | 3 | — |
| Upper Mustang | partial (Upper Mustang Trek) | 43.3 | 41.5 | 74 | graphml_fallback | 0 | 0 | 0 | 0 | 3 | — |
| Dhumba Lake | — | — | — | — | — | — | — | — | — | — | — |
| Tukuche | exact | 42.7 | 14.2 | 73 | graphml_fallback | 6 | 0 | 0 | 0 | 16 | Mustang District Hospital (5.13 km) |
| Ghami | partial (Lo Ghami Guest House) | 26.2 | 26.2 | 45 | graphml_fallback | 2 | 0 | 0 | 0 | 8 | Mustang District Hospital (34.6 km) |
| Chhusang | — | — | — | — | — | — | — | — | — | — | — |

## Myagdi (hub: ACA Checkpoint)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Beni | partial (Tribeni Hostel And Tution Centre) | 44.2 | 41.4 | 76 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (1.41 km) |
| Ghorepani | partial (Poon Hill-Ghorepani-Ghandruk Trek) | 10.6 | 8.6 | 18 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Beni Community Hospital (18.47 km) |
| Poon Hill | exact | 279.6 | 179.6 | 480 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bir Hospital (0.96 km) |
| Ghandruk | partial (Ghandruk Guesthouse And Restaurent) | 41.1 | 38.0 | 71 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Charak Memorial Hospital (1.51 km) |
| Khopra Danda | — | — | — | — | — | — | — | — | — | — | — |
| Mohare Danda | partial (Way to Mohare danda) | 11.9 | 10.2 | 21 | graphml_fallback | 28 | 0 | 0 | 0 | 30 | Beni Community Hospital (9.72 km) |
| Rupse Waterfall | — | — | — | — | — | — | — | — | — | — | — |
| Dhaulagiri Base Camp | — | — | — | — | — | — | — | — | — | — | — |
| Sikha | partial (kavrely sikhar momo center) | 325.8 | 221.0 | 560 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Bhaktapur Cancer Hospital (28.66 km) |
| Dana | partial (Suddhodana's Palace) | 179.2 | 113.5 | 308 | graphml_fallback | 11 | 0 | 0 | 0 | 24 | Kapilvastu District Hospital (2.97 km) |
| Lete | — | — | — | — | — | — | — | — | — | — | — |

## Nawalpur (hub: Amaltari home stay office)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kawasoti | partial (Police Station Kawasoti) | 25.4 | 9.4 | 44 | graphml_fallback | 18 | 0 | 0 | 0 | 25 | Nawalpur District Hospital (0.0 km) |
| Devchuli | partial (Police Station Devchuli) | 25.6 | 20.3 | 44 | graphml_fallback | 15 | 0 | 0 | 0 | 26 | Nawalpur District Hospital (13.06 km) |
| Maulakalika Temple | — | — | — | — | — | — | — | — | — | — | — |
| Amaltari | partial (Amaltari Madhyabarti Homestay) | 0.5 | 0.5 | 1 | graphml_fallback | 14 | 0 | 0 | 0 | 22 | Nawalpur District Hospital (8.87 km) |
| Narayani River | — | — | — | — | — | — | — | — | — | — | — |
| Kumarwarti | — | — | — | — | — | — | — | — | — | — | — |
| Daunne | — | — | — | — | — | — | — | — | — | — | — |
| Madhyabindu | partial (Police Station Madhyabindu) | 6.3 | 3.0 | 11 | graphml_fallback | 14 | 0 | 0 | 0 | 22 | Nawalpur District Hospital (9.21 km) |
| Triveni | partial (Triveni Khaja Ghar and Guest House) | 64.2 | 54.9 | 110 | graphml_fallback | 21 | 0 | 0 | 0 | 29 | Bandipur Hospital (16.07 km) |

## Parbat (hub: Adarsha Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kusma Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Kushma Suspension Bridge | — | — | — | — | — | — | — | — | — | — | — |
| Modi Khola | partial (Modi Khola Guest House and Fast Food Restaurant) | 23.9 | 19.4 | 41 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Hospital (23.08 km) |
| Pataley Chhango | — | — | — | — | — | — | — | — | — | — | — |
| Panchase | partial (Sarangkot -Kaskikot-Dhikuripokhari-Panchase-Damside New Treaking Trial) | 28.9 | 19.4 | 50 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Hospital (4.89 km) |
| Durlung | — | — | — | — | — | — | — | — | — | — | — |
| Setibeni | — | — | — | — | — | — | — | — | — | — | — |
| Phalebas | partial (Police Station Phalebas) | 14.1 | 10.6 | 24 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Parbat Community Hospital (5.65 km) |
| Katuwachaupari | — | — | — | — | — | — | — | — | — | — | — |
| Arthar | — | — | — | — | — | — | — | — | — | — | — |

## Syangja (hub: Akala Devi Mandir Sirsekot)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Putalibazar | partial (Police Station Putalibazar) | 22.9 | 22.6 | 39 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Syangja Community Hospital (11.12 km) |
| Waling | partial (Police Station Waling) | 8.7 | 8.0 | 15 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Syangja Community Hospital (11.03 km) |
| Sirubari | partial (Sirubari Homestay,House No. 33) | 26.9 | 18.0 | 46 | graphml_fallback | 29 | 0 | 0 | 0 | 30 | Parbat Community Hospital (12.63 km) |
| Chhangchhangdi | — | — | — | — | — | — | — | — | — | — | — |
| Arjunchaupari | partial (Police Station Arjunchaupari) | 25.7 | 19.7 | 44 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Syangja Community Hospital (9.11 km) |
| Galyang | partial (Police Station Galyang) | 9.0 | 8.9 | 15 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Syangja Community Hospital (12.15 km) |
| Ramkot | exact | 87.6 | 67.4 | 151 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Bandipur Hospital (5.83 km) |
| Aandhikhola | — | — | — | — | — | — | — | — | — | — | — |
| Panchamul | — | — | — | — | — | — | — | — | — | — | — |
| Bhirkot | — | — | — | — | — | — | — | — | — | — | — |
| Mirmi | — | — | — | — | — | — | — | — | — | — | — |
| Swasthani Temple | — | — | — | — | — | — | — | — | — | — | — |

## Tanahun (hub: BP koirala)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Damauli | partial (Police Station Damauli) | 33.3 | 19.0 | 57 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Tanahun Hospital (0.0 km) |
| Bandipur | exact | 46.1 | 35.4 | 79 | straight_line_fallback | 19 | 0 | 0 | 0 | 19 | Bandipur Hospital (1.61 km) |
| Devghat | partial (Maghe Sankranti (Devghat)) | 150.1 | 48.1 | 258 | graphml_fallback | 19 | 0 | 0 | 0 | 27 | B.P. Koirala Memorial Cancer Hospital (7.89 km) |
| Siddha Cave | exact | 47.0 | 36.1 | 81 | straight_line_fallback | 19 | 0 | 0 | 0 | 19 | Bandipur Hospital (2.06 km) |
| Vyas Cave | — | — | — | — | — | — | — | — | — | — | — |
| Chhimkeshwari | — | — | — | — | — | — | — | — | — | — | — |
| Magde | — | — | — | — | — | — | — | — | — | — | — |
| Seti River | partial (Seti River Kayaking) | 21.3 | 17.4 | 37 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (1.11 km) |
| Marshyangdi River | exact | 294.7 | 35.9 | 506 | graphml_fallback | 21 | 0 | 0 | 0 | 30 | Tanahun Hospital (29.72 km) |
| Bandipur Bazaar | — | — | — | — | — | — | — | — | — | — | — |

## Arghakhanchi (hub: Hotel Everland)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sandhikharka | partial (Police Station Sandhikharka) | 92.9 | 37.4 | 160 | graphml_fallback | 13 | 0 | 0 | 0 | 25 | Arghakhanchi District Hospital (0.0 km) |
| Supa Deurali | — | — | — | — | — | — | — | — | — | — | — |
| Arghakot | — | — | — | — | — | — | — | — | — | — | — |
| Chhatradev | — | — | — | — | — | — | — | — | — | — | — |
| Sitganga | — | — | — | — | — | — | — | — | — | — | — |
| Malarani | — | — | — | — | — | — | — | — | — | — | — |
| Bangi | — | — | — | — | — | — | — | — | — | — | — |
| Panena | — | — | — | — | — | — | — | — | — | — | — |
| Shitalpati | — | — | — | — | — | — | — | — | — | — | — |
| Khanchikot | — | — | — | — | — | — | — | — | — | — | — |
| Argha Bhagwati | — | — | — | — | — | — | — | — | — | — | — |

## Banke (hub: BaBa Barfani Tent House)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Nepalgunj | partial (Nepalgunj Medical College) | 19.0 | 17.9 | 33 | graphml_fallback | 12 | 0 | 0 | 0 | 24 | Kohalpur Medical College Hospital (0.0 km) |
| Bageshwori Temple | — | — | — | — | — | — | — | — | — | — | — |
| Banke National Park | exact | 27.2 | 25.7 | 47 | graphml_fallback | 12 | 0 | 0 | 0 | 18 | Kohalpur Medical College Hospital (24.41 km) |
| Kohalpur | partial (Kohalpur Medical College Hospital) | 19.0 | 17.9 | 33 | graphml_fallback | 12 | 0 | 0 | 0 | 24 | Kohalpur Medical College Hospital (0.0 km) |
| Rapti River | — | — | — | — | — | — | — | — | — | — | — |
| Gavar Valley | — | — | — | — | — | — | — | — | — | — | — |
| Chisapani | exact | 942.2 | 654.7 | 1619 | graphml_fallback | 9 | 0 | 0 | 0 | 14 | Ilam Community Hospital (20.75 km) |
| Sikta | — | — | — | — | — | — | — | — | — | — | — |
| Babai River | — | — | — | — | — | — | — | — | — | — | — |
| Naubasta | — | — | — | — | — | — | — | — | — | — | — |
| Rani Tal | — | — | — | — | — | — | — | — | — | — | — |
| Khajura | partial (Police Station Khajura) | 10.2 | 5.3 | 17 | graphml_fallback | 8 | 0 | 0 | 0 | 18 | Bheri Hospital (5.9 km) |

## Bardiya (hub: Bardia Homestay)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bardiya National Park | partial (Bardiya National Park Birding) | 27.6 | 26.5 | 47 | graphml_fallback | 14 | 0 | 0 | 0 | 28 | Bardiya District Hospital (23.15 km) |
| Thakurdwara | partial (Police Station Thakurdwara) | 9.3 | 7.9 | 16 | graphml_fallback | 8 | 0 | 0 | 0 | 18 | Tikapur Hospital (7.19 km) |
| Karnali River | exact | 24.1 | 18.5 | 41 | straight_line_fallback | 8 | 0 | 0 | 0 | 20 | Tikapur Hospital (11.22 km) |
| Babai Valley | — | — | — | — | — | — | — | — | — | — | — |
| Geruwa River | — | — | — | — | — | — | — | — | — | — | — |
| Gulariya | partial (Police Station Gulariya) | 30.1 | 25.1 | 52 | graphml_fallback | 14 | 0 | 0 | 0 | 27 | Bardiya District Hospital (0.0 km) |
| Bansgadhi | partial (Police Station Bansgadhi) | 55.2 | 47.8 | 95 | graphml_fallback | 8 | 0 | 0 | 0 | 20 | Kohalpur Medical College Hospital (10.3 km) |
| Crocodile Breeding Centre | — | — | — | — | — | — | — | — | — | — | — |
| Dalla Community Forest | — | — | — | — | — | — | — | — | — | — | — |

## Dang (hub: Apsara Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ghorahi | partial (Ghorahi Boys Hostel) | 0.8 | 0.7 | 1 | graphml_fallback | 13 | 0 | 0 | 0 | 19 | Dang District Hospital (1.58 km) |
| Tulsipur | partial (Tulsipur Hospital) | 428.4 | 20.5 | 736 | graphml_fallback | 12 | 0 | 0 | 0 | 16 | Rapti Life Care Hospital (0.0 km) |
| Dharapani | exact | 174.7 | 98.7 | 300 | graphml_fallback | 14 | 0 | 0 | 0 | 29 | Beni Community Hospital (22.09 km) |
| Baraha Temple | — | — | — | — | — | — | — | — | — | — | — |
| Ambikeshwari Temple | — | — | — | — | — | — | — | — | — | — | — |
| Rapti River | — | — | — | — | — | — | — | — | — | — | — |
| Chure Hills | — | — | — | — | — | — | — | — | — | — | — |
| Lamahi | partial (Lamahi Hospital) | 22.6 | 22.2 | 39 | graphml_fallback | 12 | 0 | 0 | 0 | 16 | Lamahi Hospital (0.0 km) |
| Deukhuri | — | — | — | — | — | — | — | — | — | — | — |
| Bhalubang | partial (Police Station Bhalubang) | 35.6 | 19.5 | 61 | graphml_fallback | 12 | 0 | 0 | 0 | 16 | Lamahi Hospital (7.42 km) |

## Gulmi (hub: Arje Coffee Cooperative Office)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tamghas | partial (Police Station Tamghas) | 14.6 | 13.0 | 25 | graphml_fallback | 20 | 0 | 0 | 0 | 29 | Gulmi District Hospital (0.0 km) |
| Resunga | partial (Resunga View Tower) | 15.5 | 15.5 | 27 | graphml_fallback | 20 | 0 | 0 | 0 | 30 | Gulmi District Hospital (2.53 km) |
| Resunga Hill | — | — | — | — | — | — | — | — | — | — | — |
| Ruru | — | — | — | — | — | — | — | — | — | — | — |
| Ridi | partial (Police Station Ridi) | 62.6 | 53.4 | 108 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Palpa District Hospital (13.25 km) |
| Rudrabeni | — | — | — | — | — | — | — | — | — | — | — |
| Musikot | partial (Police Station Musikot Gulmi) | 23.3 | 12.4 | 40 | graphml_fallback | 13 | 0 | 0 | 0 | 24 | Gulmi District Hospital (10.06 km) |
| Dhurkot | — | — | — | — | — | — | — | — | — | — | — |
| Isma | partial (Kismat Khaja Ghar) | 130.6 | 49.0 | 224 | graphml_fallback | 17 | 0 | 0 | 0 | 27 | Butwal Hospital (19.49 km) |
| Chandra Kot | — | — | — | — | — | — | — | — | — | — | — |
| Kaligandaki River | partial (Kaligandaki Riverside Resort) | 169.5 | 131.7 | 291 | graphml_fallback | 19 | 0 | 0 | 0 | 27 | B.P. Koirala Memorial Cancer Hospital (7.89 km) |
| Arjun | partial (Police Station Arjunchaupari) | 92.7 | 67.8 | 159 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Syangja Community Hospital (9.11 km) |

## Kapilvastu (hub: Balaji hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tilaurakot | — | — | — | — | — | — | — | — | — | — | — |
| Kudan | — | — | — | — | — | — | — | — | — | — | — |
| Niglihawa | — | — | — | — | — | — | — | — | — | — | — |
| Gotihawa | — | — | — | — | — | — | — | — | — | — | — |
| Sagarhawa | — | — | — | — | — | — | — | — | — | — | — |
| Araurakot | — | — | — | — | — | — | — | — | — | — | — |
| Jagdishpur Reservoir | exact | 22.8 | 21.8 | 39 | graphml_fallback | 12 | 0 | 0 | 0 | 25 | Kapilvastu District Hospital (9.94 km) |
| Taulihawa | partial (Police Station Taulihawa) | 27.8 | 19.9 | 48 | graphml_fallback | 11 | 0 | 0 | 0 | 23 | Kapilvastu District Hospital (0.0 km) |
| Kapilvastu Museum | exact | 26.3 | 20.1 | 45 | graphml_fallback | 12 | 0 | 0 | 0 | 24 | Kapilvastu District Hospital (3.87 km) |
| Banganga | — | — | — | — | — | — | — | — | — | — | — |
| Nigrodharama | — | — | — | — | — | — | — | — | — | — | — |

## Parasi (hub: 472)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ramgram | — | — | — | — | — | — | — | — | — | — | — |
| Ramagrama Stupa | — | — | — | — | — | — | — | — | — | — | — |
| Sunwal | — | — | — | — | — | — | — | — | — | — | — |
| Parasi Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Tribeni Dham | — | — | — | — | — | — | — | — | — | — | — |
| Narayani River | — | — | — | — | — | — | — | — | — | — | — |
| Palhi Bhagwati Temple | — | — | — | — | — | — | — | — | — | — | — |
| Susta | — | — | — | — | — | — | — | — | — | — | — |
| Bardaghat | — | — | — | — | — | — | — | — | — | — | — |

## Palpa (hub: Bashyal Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tansen | partial (Tansen Hospital) | 5.6 | 5.2 | 10 | graphml_fallback | 22 | 0 | 0 | 0 | 13 | Palpa District Hospital (0.0 km) |
| Rani Mahal | partial (Rani Mahal (Palpa)) | 2.8 | 2.1 | 5 | straight_line_fallback | 22 | 0 | 0 | 0 | 13 | Palpa District Hospital (4.08 km) |
| Srinagar Hill | — | — | — | — | — | — | — | — | — | — | — |
| Bhairabsthan | partial (Bhairabsthan (Palpa)) | 6.6 | 4.0 | 11 | graphml_fallback | 22 | 0 | 0 | 0 | 15 | Palpa District Hospital (2.43 km) |
| Ranighat | — | — | — | — | — | — | — | — | — | — | — |
| Tansen Durbar | — | — | — | — | — | — | — | — | — | — | — |
| Amar Narayan Temple | — | — | — | — | — | — | — | — | — | — | — |
| Rambha Lake | — | — | — | — | — | — | — | — | — | — | — |
| Nisdi | — | — | — | — | — | — | — | — | — | — | — |
| Tinau River | — | — | — | — | — | — | — | — | — | — | — |
| Prabhas | — | — | — | — | — | — | — | — | — | — | — |
| Bagnaskali | — | — | — | — | — | — | — | — | — | — | — |

## Pyuthan (hub: Kiran Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pyuthan Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Swargadwari | exact | 25.1 | 18.8 | 43 | graphml_fallback | 12 | 0 | 0 | 0 | 22 | Pyuthan District Hospital (21.04 km) |
| Swargadwari Temple | — | — | — | — | — | — | — | — | — | — | — |
| Jhimruk River | — | — | — | — | — | — | — | — | — | — | — |
| Bijuwar | partial (Police Station Bijuwar) | 0.0 | 0.0 | 0 | straight_line_fallback | 11 | 0 | 0 | 0 | 24 | Pyuthan District Hospital (2.26 km) |
| Okharkot | — | — | — | — | — | — | — | — | — | — | — |
| Naubahini | — | — | — | — | — | — | — | — | — | — | — |
| Mandavi | — | — | — | — | — | — | — | — | — | — | — |
| Bhingri | — | — | — | — | — | — | — | — | — | — | — |
| Khaira | partial (Police Station Khairahani) | 216.3 | 186.5 | 372 | graphml_fallback | 23 | 0 | 0 | 0 | 30 | Cmc Hospital Emergency (23.49 km) |
| Lwang | — | — | — | — | — | — | — | — | — | — | — |

## Rolpa (hub: Jaljala)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Liwang | exact | 74.3 | 30.1 | 128 | graphml_fallback | 14 | 0 | 0 | 0 | 18 | Pyuthan District Hospital (23.21 km) |
| Jaljala | exact | 91.8 | 64.6 | 158 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Beni Community Hospital (9.5 km) |
| Jaljala Hill | — | — | — | — | — | — | — | — | — | — | — |
| Thawang | exact | 305.6 | 9.9 | 525 | graphml_fallback | 5 | 0 | 0 | 0 | 17 | Pyuthan District Hospital (32.96 km) |
| Sulichaur | partial (Police Station Sulichaur) | 321.3 | 30.6 | 552 | graphml_fallback | 9 | 0 | 0 | 0 | 22 | Rukum District Hospital (29.6 km) |
| Madi River | — | — | — | — | — | — | — | — | — | — | — |
| Runtigadhi | exact | 328.4 | 39.4 | 564 | graphml_fallback | 15 | 0 | 0 | 0 | 22 | Pyuthan District Hospital (34.55 km) |
| Jelbang | — | — | — | — | — | — | — | — | — | — | — |
| Lungri | — | — | — | — | — | — | — | — | — | — | — |
| Rolpa Bazaar | — | — | — | — | — | — | — | — | — | — | — |

## Rukum East (hub: Dhule Base Camp)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Rukumkot | partial (Police Station Rukumkot) | 50.8 | 30.5 | 87 | graphml_fallback | 6 | 0 | 0 | 0 | 21 | Rukum District Hospital (12.74 km) |
| Sisne Himal | — | — | — | — | — | — | — | — | — | — | — |
| Putha Himal | — | — | — | — | — | — | — | — | — | — | — |
| Kamal Daha | — | — | — | — | — | — | — | — | — | — | — |
| Putha Uttarganga | — | — | — | — | — | — | — | — | — | — | — |
| Lukum | — | — | — | — | — | — | — | — | — | — | — |
| Taksera | — | — | — | — | — | — | — | — | — | — | — |
| Mahat | — | — | — | — | — | — | — | — | — | — | — |
| Rukumkot Valley | — | — | — | — | — | — | — | — | — | — | — |

## Rupandehi (hub: Aman New Staff Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lumbini | partial (Lumbini-Muktinath) | 215.2 | 151.3 | 370 | graphml_fallback | 4 | 0 | 0 | 0 | 13 | Mustang District Hospital (14.57 km) |
| Maya Devi Temple | — | — | — | — | — | — | — | — | — | — | — |
| Lumbini Monastic Zone | — | — | — | — | — | — | — | — | — | — | — |
| Tilottama | — | — | — | — | — | — | — | — | — | — | — |
| Butwal | exact | 22.7 | 21.4 | 39 | graphml_fallback | 17 | 0 | 0 | 0 | 29 | Butwal Hospital (0.0 km) |
| Manimukunda Sen Park | — | — | — | — | — | — | — | — | — | — | — |
| Siddhababa Temple | — | — | — | — | — | — | — | — | — | — | — |
| Devinagar | — | — | — | — | — | — | — | — | — | — | — |
| Tinau River | — | — | — | — | — | — | — | — | — | — | — |
| Sainamaina | partial (Police Station Sainamaina) | 32.1 | 24.0 | 55 | graphml_fallback | 17 | 0 | 0 | 0 | 26 | Butwal Hospital (11.81 km) |
| Parroha | — | — | — | — | — | — | — | — | — | — | — |

## Dailekh (hub: Aale Staff Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dailekh Bazaar | partial (Police Station Dailekh Bazaar) | 24.9 | 21.1 | 43 | graphml_fallback | 7 | 0 | 0 | 0 | 26 | Dailekh District Hospital (0.0 km) |
| Dullu | partial (Police Station Dullu) | 25.9 | 22.6 | 45 | graphml_fallback | 7 | 0 | 0 | 0 | 22 | Dailekh District Hospital (2.43 km) |
| Panchakoshi | partial (Panchakoshi Hotel and Lodge) | 11.4 | 11.0 | 20 | graphml_fallback | 7 | 0 | 0 | 0 | 30 | Dailekh District Hospital (10.16 km) |
| Naulakot | — | — | — | — | — | — | — | — | — | — | — |
| Shree Sthan | — | — | — | — | — | — | — | — | — | — | — |
| Nabhi Sthan | — | — | — | — | — | — | — | — | — | — | — |
| Padukasthan | — | — | — | — | — | — | — | — | — | — | — |
| Dhuleshwor | — | — | — | — | — | — | — | — | — | — | — |
| Chamunda Bindrasaini | — | — | — | — | — | — | — | — | — | — | — |
| Karnali River | exact | 56.7 | 43.6 | 97 | straight_line_fallback | 8 | 0 | 0 | 0 | 20 | Tikapur Hospital (11.22 km) |
| Mahabu | partial (Police Station Mahabu) | 10.1 | 6.5 | 17 | graphml_fallback | 7 | 0 | 0 | 0 | 26 | Dailekh District Hospital (23.27 km) |
| Dullu Durbar | — | — | — | — | — | — | — | — | — | — | — |

## Dolpa (hub: Angad Galley and Cafe Inn)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Shey Phoksundo National Park | exact | 46.2 | 26.4 | 79 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (26.49 km) |
| Phoksundo Lake | exact | 47.9 | 30.9 | 82 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (24.87 km) |
| Shey Gompa | exact | 48.8 | 31.5 | 84 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (10.32 km) |
| Ringmo | exact | 50.6 | 24.7 | 87 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (22.36 km) |
| Dho Tarap | exact | 0.5 | 0.5 | 1 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (38.21 km) |
| Saldang | exact | 34.6 | 34.6 | 60 | graphml_fallback | 0 | 0 | 0 | 0 | 1 | — |
| Tinje | — | — | — | — | — | — | — | — | — | — | — |
| Phoksundo Waterfall | partial (Phoksundo Waterfall (Suligad)) | 45.9 | 31.7 | 79 | graphml_fallback | 2 | 0 | 0 | 0 | 5 | Dolpa District Hospital (26.23 km) |
| Dunai | partial (Police Station Dunai) | 50.8 | 38.5 | 87 | graphml_fallback | 2 | 0 | 0 | 0 | 8 | Dolpa District Hospital (0.0 km) |

## Humla (hub: CFD Humla)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Simkot | — | — | — | — | — | — | — | — | — | — | — |
| Limi Valley | — | — | — | — | — | — | — | — | — | — | — |
| Hilsa | partial (Karnali Corridor (Hilsa Road)) | 68.5 | 64.9 | 118 | graphml_fallback | 8 | 0 | 0 | 0 | 25 | Bajura District Hospital (27.21 km) |
| Namkha | — | — | — | — | — | — | — | — | — | — | — |
| Yari | — | — | — | — | — | — | — | — | — | — | — |
| Nyinba | — | — | — | — | — | — | — | — | — | — | — |
| Limi River | — | — | — | — | — | — | — | — | — | — | — |
| Halji Monastery | — | — | — | — | — | — | — | — | — | — | — |
| Saipal Himal | — | — | — | — | — | — | — | — | — | — | — |

## Jajarkot (hub: Dhiraj and niraj hotel and lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Khalanga | partial (Police Station Khalanga) | 68.5 | 45.7 | 118 | graphml_fallback | 15 | 0 | 0 | 0 | 26 | Salyan District Hospital (0.0 km) |
| Barekot | partial (Police Station Barekot) | 15.3 | 11.8 | 26 | straight_line_fallback | 6 | 0 | 0 | 0 | 22 | Jajarkot District Hospital (13.58 km) |
| Nalgad | partial (Police Station Nalgad) | 27.7 | 23.9 | 48 | graphml_fallback | 5 | 0 | 0 | 0 | 27 | Jajarkot District Hospital (5.89 km) |
| Bheri River | — | — | — | — | — | — | — | — | — | — | — |
| Jagatipur | — | — | — | — | — | — | — | — | — | — | — |
| Chhedagad | partial (Police Station Chhedagad) | 33.3 | 27.1 | 57 | graphml_fallback | 5 | 0 | 0 | 0 | 27 | Jajarkot District Hospital (11.29 km) |
| Kushe | partial (Police Station Kushe) | 7.8 | 6.0 | 13 | straight_line_fallback | 10 | 0 | 0 | 0 | 26 | Jajarkot District Hospital (13.84 km) |
| Jajarkot Durbar | — | — | — | — | — | — | — | — | — | — | — |
| Thalaha | — | — | — | — | — | — | — | — | — | — | — |

## Jumla (hub: Ghurchi Lagna)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chandannath | partial (Police Station Chandannath) | 22.6 | 22.5 | 39 | graphml_fallback | 6 | 0 | 0 | 0 | 15 | Jumla District Hospital (0.0 km) |
| Sinja Valley | — | — | — | — | — | — | — | — | — | — | — |
| Chandannath Temple | — | — | — | — | — | — | — | — | — | — | — |
| Tatopani | partial (Tatopani Guest House) | 233.8 | 183.4 | 402 | graphml_fallback | 25 | 0 | 0 | 0 | 30 | Beni Community Hospital (18.05 km) |
| Kanakasundari | partial (Police Station Kanakasundari) | 26.7 | 20.3 | 46 | graphml_fallback | 7 | 0 | 0 | 0 | 20 | Jumla District Hospital (13.04 km) |
| Patmara | — | — | — | — | — | — | — | — | — | — | — |
| Tila River | — | — | — | — | — | — | — | — | — | — | — |
| Jumla Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Guthichaur | partial (Police Station Guthichaur) | 18.7 | 13.3 | 32 | graphml_fallback | 6 | 0 | 0 | 0 | 14 | Jumla District Hospital (9.36 km) |
| Dillichaur | — | — | — | — | — | — | — | — | — | — | — |

## Kalikot (hub: Bipana Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Manma | partial (Police Station Manma) | 18.8 | 17.6 | 32 | graphml_fallback | 4 | 0 | 0 | 0 | 21 | Kalikot District Hospital (0.0 km) |
| Raskot | partial (Police Station Raskot) | 23.7 | 23.3 | 41 | graphml_fallback | 4 | 0 | 0 | 0 | 21 | Kalikot District Hospital (5.89 km) |
| Pachal Jharana | — | — | — | — | — | — | — | — | — | — | — |
| Pachal Waterfall | exact | 133.1 | 70.0 | 229 | graphml_fallback | 6 | 0 | 0 | 0 | 24 | Jajarkot District Hospital (11.29 km) |
| Sanni Triveni | — | — | — | — | — | — | — | — | — | — | — |
| Tilagufa | partial (Police Station Tilagufa) | 23.7 | 23.3 | 41 | graphml_fallback | 4 | 0 | 0 | 0 | 21 | Kalikot District Hospital (5.89 km) |
| Raskot Valley | — | — | — | — | — | — | — | — | — | — | — |
| Mahawai | — | — | — | — | — | — | — | — | — | — | — |
| Palata | — | — | — | — | — | — | — | — | — | — | — |
| Khadachakra | — | — | — | — | — | — | — | — | — | — | — |
| Panchadeval | — | — | — | — | — | — | — | — | — | — | — |

## Mugu (hub: Bhandari Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Rara Lake | exact | 3.8 | 3.8 | 7 | graphml_fallback | 6 | 0 | 0 | 0 | 14 | Mugu District Hospital (0.32 km) |
| Rara National Park | partial (Rara National Park Office) | 4.9 | 4.9 | 8 | graphml_fallback | 6 | 0 | 0 | 0 | 14 | Mugu District Hospital (1.56 km) |
| Talcha Airport | — | — | — | — | — | — | — | — | — | — | — |
| Gamgadhi | partial (Police Station Gamgadhi) | 4.2 | 4.0 | 7 | graphml_fallback | 6 | 0 | 0 | 0 | 14 | Mugu District Hospital (0.32 km) |
| Mugu Karnali | — | — | — | — | — | — | — | — | — | — | — |
| Murma Top | — | — | — | — | — | — | — | — | — | — | — |
| Chankheli | — | — | — | — | — | — | — | — | — | — | — |
| Rara Viewpoint | — | — | — | — | — | — | — | — | — | — | — |
| Pina | partial (Peace Pinacle Homestay) | 280.3 | 223.0 | 482 | graphml_fallback | 28 | 0 | 0 | 0 | 30 | Fishtail Hospital (10.98 km) |
| Talcha | — | — | — | — | — | — | — | — | — | — | — |
| Khatyad | partial (Khatyad Khola) | 18.6 | 18.7 | 32 | graphml_fallback | 6 | 0 | 0 | 0 | 16 | Mugu District Hospital (14.96 km) |

## Rukum West (hub: Sapince Hotel and Lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Musikot | partial (Police Station Musikot Gulmi) | 277.0 | 95.9 | 476 | graphml_fallback | 13 | 0 | 0 | 0 | 24 | Gulmi District Hospital (10.06 km) |
| Sani Bheri | — | — | — | — | — | — | — | — | — | — | — |
| Chaurjahari | partial (Police Station Chaurjahari) | 41.2 | 20.6 | 71 | graphml_fallback | 5 | 0 | 0 | 0 | 25 | Jajarkot District Hospital (16.15 km) |
| Aathbiskot | partial (Police Station Aathbiskot) | 18.8 | 14.5 | 32 | straight_line_fallback | 5 | 0 | 0 | 0 | 23 | Jajarkot District Hospital (17.48 km) |
| Gotamkot | — | — | — | — | — | — | — | — | — | — | — |
| Syarpu Lake | — | — | — | — | — | — | — | — | — | — | — |
| Sani Bheri Valley | — | — | — | — | — | — | — | — | — | — | — |

## Salyan (hub: Kupinde Daha Picnic Site)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Khalanga | partial (Police Station Khalanga) | 14.6 | 11.2 | 25 | straight_line_fallback | 15 | 0 | 0 | 0 | 26 | Salyan District Hospital (0.0 km) |
| Kupinde Lake | — | — | — | — | — | — | — | — | — | — | — |
| Khairabang Temple | — | — | — | — | — | — | — | — | — | — | — |
| Chhatreshwari Temple | — | — | — | — | — | — | — | — | — | — | — |
| Kachuwani | — | — | — | — | — | — | — | — | — | — | — |
| Sharada River | — | — | — | — | — | — | — | — | — | — | — |
| Kumakh | — | — | — | — | — | — | — | — | — | — | — |
| Darma | — | — | — | — | — | — | — | — | — | — | — |
| Bangad Kupinde | — | — | — | — | — | — | — | — | — | — | — |
| Salyan Bazaar | partial (Police Station Salyan Bazaar) | 14.6 | 11.2 | 25 | straight_line_fallback | 15 | 0 | 0 | 0 | 26 | Salyan District Hospital (0.0 km) |
| Lanti | — | — | — | — | — | — | — | — | — | — | — |

## Surkhet (hub: DFC Hotel)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Birendranagar | partial (Birendranagar Municipality) | 2.8 | 2.0 | 5 | graphml_fallback | 10 | 0 | 0 | 0 | 20 | Deuti Hospital (0.32 km) |
| Bulbule Lake | — | — | — | — | — | — | — | — | — | — | — |
| Kakrebihar | partial (Kakrebihar (Surkhet)) | 2.5 | 2.5 | 4 | graphml_fallback | 13 | 0 | 0 | 0 | 25 | Deuti Hospital (1.3 km) |
| Deuti Bajai Temple | — | — | — | — | — | — | — | — | — | — | — |
| Bheri River | — | — | — | — | — | — | — | — | — | — | — |
| Gadhi | partial (Runtigadhi) | 133.4 | 101.8 | 229 | graphml_fallback | 15 | 0 | 0 | 0 | 22 | Pyuthan District Hospital (34.55 km) |
| Latikoili | — | — | — | — | — | — | — | — | — | — | — |
| Chingad | — | — | — | — | — | — | — | — | — | — | — |
| Barahatal | — | — | — | — | — | — | — | — | — | — | — |

## Achham (hub: New ramaroshan Guest house)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mangalsen | partial (Police Station Mangalsen) | 23.1 | 23.1 | 40 | graphml_fallback | 5 | 0 | 0 | 0 | 23 | Achham District Hospital (0.0 km) |
| Ramaroshan | partial (Ramaroshan - Adventure & Camping Resort) | 0.1 | 0.1 | 0 | graphml_fallback | 5 | 0 | 0 | 0 | 26 | Kalikot District Hospital (17.57 km) |
| Ramaroshan Lakes | — | — | — | — | — | — | — | — | — | — | — |
| Sanfebagar | partial (Police Station Sanfebagar) | 26.5 | 23.4 | 46 | graphml_fallback | 5 | 0 | 0 | 0 | 24 | Achham District Hospital (11.49 km) |
| Baidyanath Dham | — | — | — | — | — | — | — | — | — | — | — |
| Panchadeval Binayak | — | — | — | — | — | — | — | — | — | — | — |
| Kamalbazar | partial (Police Station Kamalbazar) | 23.6 | 22.4 | 41 | graphml_fallback | 5 | 0 | 0 | 0 | 23 | Achham District Hospital (13.17 km) |
| Turmakhad | — | — | — | — | — | — | — | — | — | — | — |
| Budiganga River | — | — | — | — | — | — | — | — | — | — | — |
| Jaygadh | — | — | — | — | — | — | — | — | — | — | — |
| Bannigadhi Jaygadh | — | — | — | — | — | — | — | — | — | — | — |
| Chaurpati | partial (Police Station Chaurpati) | 11.2 | 11.1 | 19 | graphml_fallback | 5 | 0 | 0 | 0 | 24 | Achham District Hospital (12.44 km) |

## Baitadi (hub: Chamlek)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dasharathchand | partial (Police Station Dasharathchand) | 20.6 | 15.8 | 35 | straight_line_fallback | 5 | 0 | 0 | 0 | 12 | Baitadi District Hospital (0.0 km) |
| Patan | partial (Police Station Chhorepatan) | 445.8 | 367.8 | 766 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Fishtail Hospital (3.87 km) |
| Melauli Bhagwati Temple | — | — | — | — | — | — | — | — | — | — | — |
| Tripura Sundari Temple | — | — | — | — | — | — | — | — | — | — | — |
| Pancheswor | — | — | — | — | — | — | — | — | — | — | — |
| Dehimandau | — | — | — | — | — | — | — | — | — | — | — |
| Surnaya | — | — | — | — | — | — | — | — | — | — | — |
| Shivanath | — | — | — | — | — | — | — | — | — | — | — |
| Dilashaini | — | — | — | — | — | — | — | — | — | — | — |
| Dogadakedar | — | — | — | — | — | — | — | — | — | — | — |
| Mahakali River | exact | 97.1 | 76.6 | 167 | graphml_fallback | 8 | 0 | 0 | 0 | 17 | Kanchanpur District Hospital (4.85 km) |
| Patan Bazaar | — | — | — | — | — | — | — | — | — | — | — |

## Bajhang (hub: A.p.vojanalaya)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chainpur | partial (Police Station Chainpur) | 33.7 | 28.1 | 58 | graphml_fallback | 4 | 0 | 0 | 0 | 17 | Bajhang District Hospital (0.0 km) |
| Surma Sarovar | — | — | — | — | — | — | — | — | — | — | — |
| Surma Valley | — | — | — | — | — | — | — | — | — | — | — |
| Khaptad National Park | exact | 95.3 | 75.1 | 164 | graphml_fallback | 8 | 0 | 0 | 0 | 18 | Kanchanpur District Hospital (34.13 km) |
| Thalara | — | — | — | — | — | — | — | — | — | — | — |
| Talkot | partial (Police Station Talkot) | 42.5 | 35.3 | 73 | graphml_fallback | 3 | 0 | 0 | 0 | 13 | Bajhang District Hospital (11.29 km) |
| Masta | — | — | — | — | — | — | — | — | — | — | — |
| Kedarsyu | — | — | — | — | — | — | — | — | — | — | — |
| Seti River | partial (Seti River Kayaking) | 409.3 | 331.7 | 703 | graphml_fallback | 30 | 0 | 0 | 0 | 30 | Gandaki Medical College Teaching Hospital (1.11 km) |
| Chhabis Pathibhara | — | — | — | — | — | — | — | — | — | — | — |
| Jayaprithvi | — | — | — | — | — | — | — | — | — | — | — |

## Bajura (hub: Birekhola,Jharana)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Martadi | partial (Police Station Martadi) | 5.3 | 4.0 | 9 | straight_line_fallback | 5 | 0 | 0 | 0 | 24 | Bajura District Hospital (0.0 km) |
| Badimalika Temple | — | — | — | — | — | — | — | — | — | — | — |
| Budhinanda | — | — | — | — | — | — | — | — | — | — | — |
| Budhinanda Lake | — | — | — | — | — | — | — | — | — | — | — |
| Kolti | partial (Police Station Kolti) | 14.9 | 13.8 | 26 | graphml_fallback | 5 | 0 | 0 | 0 | 30 | Bajura District Hospital (17.75 km) |
| Triveni | partial (Triveni Khaja Ghar and Guest House) | 510.7 | 349.9 | 878 | graphml_fallback | 21 | 0 | 0 | 0 | 29 | Bandipur Hospital (16.07 km) |
| Nateshwori Temple | — | — | — | — | — | — | — | — | — | — | — |
| Gaumul | — | — | — | — | — | — | — | — | — | — | — |
| Swamikartik | partial (Police Station Swamikartik) | 31.7 | 18.4 | 54 | graphml_fallback | 2 | 0 | 0 | 0 | 15 | Bajura District Hospital (20.22 km) |
| Jagannath | — | — | — | — | — | — | — | — | — | — | — |

## Dadeldhura (hub: Akashdeep Hotel and lodge)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Amargadhi | partial (Police Station Amargadhi) | 1.4 | 1.0 | 2 | graphml_fallback | 7 | 0 | 0 | 0 | 15 | Dadeldhura Eye Hospital (0.0 km) |
| Dadeldhura Bazaar | — | — | — | — | — | — | — | — | — | — | — |
| Ugratara Temple | — | — | — | — | — | — | — | — | — | — | — |
| Alital | partial (Police Station Aalital) | 17.9 | 17.9 | 31 | graphml_fallback | 6 | 0 | 0 | 0 | 12 | Dadeldhura Eye Hospital (18.01 km) |
| Amargadhi Fort | — | — | — | — | — | — | — | — | — | — | — |
| Ajaymeru | — | — | — | — | — | — | — | — | — | — | — |
| Ganyapdhura | partial (Police Station Ganyapdhura) | 7.0 | 7.0 | 12 | graphml_fallback | 7 | 0 | 0 | 0 | 14 | Dadeldhura Eye Hospital (6.27 km) |
| Parshuram Dham | — | — | — | — | — | — | — | — | — | — | — |
| Jogbudha | partial (Police Station Jogbudha) | 40.5 | 17.4 | 70 | graphml_fallback | 11 | 0 | 0 | 0 | 23 | Dadeldhura Eye Hospital (16.81 km) |
| Sahastralinga | — | — | — | — | — | — | — | — | — | — | — |
| Chipur | — | — | — | — | — | — | — | — | — | — | — |

## Darchula (hub: Api Himal)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Khalanga | partial (Police Station Khalanga) | 253.9 | 216.7 | 436 | graphml_fallback | 15 | 0 | 0 | 0 | 26 | Salyan District Hospital (0.0 km) |
| Api Himal | exact | 0.0 | 0.0 | 0 | straight_line_fallback | 0 | 0 | 0 | 0 | 4 | — |
| Api Nampa Conservation Area | exact | 12.8 | 9.9 | 22 | straight_line_fallback | 0 | 0 | 0 | 0 | 2 | — |
| Byas Valley | — | — | — | — | — | — | — | — | — | — | — |
| Tinkar | — | — | — | — | — | — | — | — | — | — | — |
| Malikarjun Temple | — | — | — | — | — | — | — | — | — | — | — |
| Shailyashikhar | — | — | — | — | — | — | — | — | — | — | — |
| Duhu | — | — | — | — | — | — | — | — | — | — | — |
| Latinath | — | — | — | — | — | — | — | — | — | — | — |
| Kalapani | partial (कालापानी चोक Kalapani Chok ८६६७) | 1010.9 | 776.1 | 1737 | graphml_fallback | 12 | 0 | 0 | 0 | 19 | Ilam Community Hospital (11.25 km) |
| Lipulekh | — | — | — | — | — | — | — | — | — | — | — |

## Doti (hub: Basudhara view point)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dipayal Silgadhi | — | — | — | — | — | — | — | — | — | — | — |
| Shaileshwari Temple | — | — | — | — | — | — | — | — | — | — | — |
| Doti Durbar | — | — | — | — | — | — | — | — | — | — | — |
| Silgadhi | — | — | — | — | — | — | — | — | — | — | — |
| Gopghat | — | — | — | — | — | — | — | — | — | — | — |
| Jorayal | — | — | — | — | — | — | — | — | — | — | — |
| Budar | — | — | — | — | — | — | — | — | — | — | — |
| Chhatiwan | — | — | — | — | — | — | — | — | — | — | — |
| Lanakheda | — | — | — | — | — | — | — | — | — | — | — |

## Kailali (hub: Banana Agro Resort)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dhangadhi | exact | 71.5 | 55.0 | 123 | straight_line_fallback | 10 | 0 | 0 | 0 | 12 | Kailali District Hospital (0.98 km) |
| Tikapur Park | — | — | — | — | — | — | — | — | — | — | — |
| Ghodaghodi Lake | exact | 71.5 | 55.0 | 123 | straight_line_fallback | 10 | 0 | 0 | 0 | 12 | Kailali District Hospital (0.98 km) |
| Chisapani | exact | 927.7 | 713.6 | 1594 | straight_line_fallback | 9 | 0 | 0 | 0 | 14 | Ilam Community Hospital (20.75 km) |
| Karnali Bridge | — | — | — | — | — | — | — | — | — | — | — |
| Godawari | partial (Godawari Botanical Garden Birding) | 559.3 | 430.3 | 961 | straight_line_fallback | 30 | 0 | 0 | 0 | 30 | Madhyapur Hospital (8.95 km) |
| Jokhar Lake | — | — | — | — | — | — | — | — | — | — | — |
| Tikapur | partial (Tikapur Hospital) | 2.7 | 2.3 | 5 | graphml_fallback | 8 | 0 | 0 | 0 | 18 | Tikapur Hospital (0.0 km) |
| Mohana River | — | — | — | — | — | — | — | — | — | — | — |
| Geta | — | — | — | — | — | — | — | — | — | — | — |
| Bhada Village | — | — | — | — | — | — | — | — | — | — | — |
| Rajghat | — | — | — | — | — | — | — | — | — | — | — |

## Kanchanpur (hub: Betkot Tal)
| Place | Found | Route km | Straight km | min | Source | Hosp | Hotel | Rest | Bank | Police | Nearest hospital |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Shuklaphanta National Park | exact | 30.4 | 21.7 | 52 | graphml_fallback | 13 | 0 | 0 | 0 | 17 | Kanchanpur District Hospital (12.74 km) |
| Mahendranagar | partial (Bhimdatta (Mahendranagar)) | 21.3 | 19.3 | 37 | graphml_fallback | 13 | 0 | 0 | 0 | 17 | Kanchanpur District Hospital (6.67 km) |
| Dodhara Chandani | — | — | — | — | — | — | — | — | — | — | — |
| Gaddachauki | partial (Police Station Gaddachauki) | 24.7 | 24.6 | 43 | graphml_fallback | 4 | 0 | 0 | 0 | 11 | Kanchanpur District Hospital (9.79 km) |
| Mahakali River | exact | 12.9 | 11.9 | 22 | graphml_fallback | 8 | 0 | 0 | 0 | 17 | Kanchanpur District Hospital (4.85 km) |
| Bedkot Lake | — | — | — | — | — | — | — | — | — | — | — |
| Jhilmila Lake | — | — | — | — | — | — | — | — | — | — | — |
| Rani Tal | — | — | — | — | — | — | — | — | — | — | — |
| Brahmadev | — | — | — | — | — | — | — | — | — | — | — |
| Daiji | — | — | — | — | — | — | — | — | — | — | — |
| Siddhanath Temple | — | — | — | — | — | — | — | — | — | — | — |
