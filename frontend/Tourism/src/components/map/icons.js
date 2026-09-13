import L from "leaflet"

const shadowSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 18" width="40" height="18">
  <ellipse cx="20" cy="9" rx="16" ry="6" fill="#000000" fill-opacity="0.25"/>
</svg>`
const shadowDataUrl = `data:image/svg+xml;utf8,${encodeURIComponent(shadowSvg)}`

const makeSvgIcon = (colorHex, letter = "") => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 42" width="32" height="42">
    <path fill="${colorHex}" stroke="#FFFFFF" stroke-width="2" d="M16 0C7.163 0 0 7.163 0 16c0 12 16 26 16 26s16-14 16-26C32 7.163 24.837 0 16 0z"/>
    <circle cx="16" cy="15" r="7" fill="#FFFFFF"/>
    ${letter ? `<text x="16" y="19" font-size="10" font-weight="900" font-family="sans-serif" text-anchor="middle" fill="${colorHex}">${letter}</text>` : `<circle cx="16" cy="15" r="4" fill="${colorHex}"/>`}
  </svg>`
  const iconUrl = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
  return new L.Icon({
    iconUrl,
    shadowUrl: shadowDataUrl,
    iconSize: [32, 42],
    iconAnchor: [16, 42],
    popupAnchor: [0, -38],
    shadowSize: [32, 16],
    shadowAnchor: [16, 8],
  })
}

export const userIcon = makeSvgIcon("#2563EB", "U")
export const destinationIcon = makeSvgIcon("#DC2626", "D")
export const hospitalIcon = makeSvgIcon("#059669", "+")
export const policeIcon = makeSvgIcon("#7C3AED", "P")
export const attractionIcon = makeSvgIcon("#D97706", "★")

export const createCustomIcon = (colorHex, label = "") => makeSvgIcon(colorHex, label)
export default makeSvgIcon
