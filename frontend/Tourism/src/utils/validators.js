/**
 * Input validators for place submission, coordinates, and feedback
 */
export const validators = {
  isEmail: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
  isPhone: (val) => /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/.test(val),
  isValidCoordinate: (lat, lon) => {
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    return !isNaN(latNum) && !isNaN(lonNum) && latNum >= -90 && latNum <= 90 && lonNum >= -180 && lonNum <= 180;
  },
  isPositiveNumber: (val) => !isNaN(parseFloat(val)) && parseFloat(val) >= 0,
  isNotEmpty: (val) => val != null && String(val).trim().length > 0,
};
export default validators;
