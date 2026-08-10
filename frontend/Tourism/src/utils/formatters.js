/**
 * String and Number formatting utilities
 */
export const formatCurrencyNPR = (amount) => {
  const num = Number(amount) || 0;
  return `रू ${num.toLocaleString('en-IN')}`;
};

export const formatCurrencyUSD = (amount) => {
  const num = Number(amount) || 0;
  return `$${num.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
};

export const formatDistanceKM = (km) => {
  const num = Number(km);
  if (isNaN(num)) return '--';
  return num < 1 ? `${Math.round(num * 1000)} m` : `${num.toFixed(1)} km`;
};

export const formatDurationMin = (min) => {
  const num = Number(min);
  if (isNaN(num)) return '--';
  const hours = Math.floor(num / 60);
  const minutes = Math.round(num % 60);
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes} min`;
};
