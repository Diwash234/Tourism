/**
 * Legacy local destination catalogue.
 *
 * Public destination records now come from the API. This module intentionally
 * contains no sample destinations, ratings, prices, coordinates or images so
 * an old consumer cannot reintroduce fabricated records as a fallback.
 */
const nepalDestinations = []

export default nepalDestinations

export const searchDestinations = () => []

export const getDestinationById = () => null
