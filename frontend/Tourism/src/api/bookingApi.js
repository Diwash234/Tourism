import axiosClient from "./axiosClient";

const bookingApi = {
  getMyBookings: () => axiosClient.get("/bookings/"),
  getBooking: (id) => axiosClient.get(`/bookings/${id}/`),
  createBooking: (payload) => axiosClient.post("/bookings/", payload),
  cancelBooking: (id) => axiosClient.post(`/bookings/${id}/cancel/`),
  confirmBooking: (id) => axiosClient.post(`/bookings/${id}/confirm/`),
  addHotelReview: (hotelId, rating, comment) =>
    axiosClient.post("/hotel-reviews/", { hotel: hotelId, rating, comment }),
  listHotels: (destinationId) => axiosClient.get("/hotels/", { params: { destination: destinationId } }),
};

export default bookingApi;
