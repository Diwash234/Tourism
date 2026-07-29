// Covers OSM-nearby places, navigation routes, and weather-by-coordinates
// — spread across navigationApi.js and nearbyApi.js today. Re-exported
// together here since the spec asked for a single mapService.
import navigationApi from "../api/navigationApi"
import nearbyApi from "../api/nearbyApi"

const mapService = {
  ...navigationApi,
  ...nearbyApi,
}

export default mapService