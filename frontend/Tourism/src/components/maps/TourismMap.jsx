// Thin re-export so the component lives at the path the design spec
// expects (components/maps/TourismMap.jsx) while reusing the existing,
// already-wired Leaflet implementation in components/map/MapView.jsx.
// If/when route-optimization variants (safest/cheapest/shortest/trekking)
// are added, build them here as props on top of MapView rather than
// forking the marker/icon logic.
export { default } from "../map/MapView"