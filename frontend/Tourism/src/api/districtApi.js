import axiosClient from "./axiosClient";

// Administrative geography API (task-79 §5/§24): 7 provinces, 77 districts.
const districtApi = {
  provinces: () => axiosClient.get("/provinces/"),
  districts: (params) => axiosClient.get("/districts/", { params }),
  district: (slug) => axiosClient.get(`/districts/${slug}/`),
};

export default districtApi;
