import { Navigate } from "react-router-dom"

/**
 * Legacy route compatibility. The planner is rendered by the dataset-driven
 * Itinerary page; keeping this redirect avoids a second client-side budget
 * calculator with sample prices and duplicated destination data.
 */
export default function TripPlanner() {
  return <Navigate to="/itinerary" replace />
}
