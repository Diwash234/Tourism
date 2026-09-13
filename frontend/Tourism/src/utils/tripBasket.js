const KEY = "tourism_trip_basket"

export function getTripBasket() {
  try {
    const rows = JSON.parse(localStorage.getItem(KEY) || "[]")
    return Array.isArray(rows) ? rows.slice(0, 12) : []
  } catch {
    return []
  }
}

export function saveTripBasket(items) {
  localStorage.setItem(KEY, JSON.stringify((items || []).slice(0, 12)))
  return getTripBasket()
}

export function addToTripBasket(listing, quantity = 1) {
  if (!listing?.id) return getTripBasket()
  const items = getTripBasket()
  const existing = items.find((row) => row.listing_id === listing.id)
  if (existing) existing.quantity = Math.min(20, (existing.quantity || 1) + quantity)
  else {
    items.push({
      listing_id: listing.id,
      slug: listing.slug,
      title: listing.title,
      kind: listing.kind,
      price_npr: listing.price_npr,
      currency: listing.currency || "NPR",
      image_url: listing.image_url || "",
      partner_name: listing.partner_name || "",
      quantity: Math.max(1, quantity),
    })
  }
  return saveTripBasket(items)
}

export function removeFromTripBasket(listingId) {
  return saveTripBasket(getTripBasket().filter((row) => row.listing_id !== listingId))
}

export function clearTripBasket() {
  localStorage.removeItem(KEY)
  return []
}

export function basketTotal(items = getTripBasket()) {
  return items.reduce((sum, row) => sum + Number(row.price_npr || 0) * Number(row.quantity || 1), 0)
}
