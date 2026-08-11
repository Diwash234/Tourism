/**
 * Image handling, preview generators, and fallbacks
 */
export const NEPAL_DEFAULT_HERO = "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80";

export const getDestinationImageUrl = (destination) => {
  if (!destination) return NEPAL_DEFAULT_HERO;
  if (destination.cover_image_url) return destination.cover_image_url;
  if (destination.gallery && destination.gallery.length > 0) {
    const first = destination.gallery[0];
    return first.image || first.external_url || first.display_url || NEPAL_DEFAULT_HERO;
  }
  return NEPAL_DEFAULT_HERO;
};

export const createLocalImagePreview = (file) => {
  if (!file) return null;
  return URL.createObjectURL(file);
};
