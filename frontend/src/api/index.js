const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    // Handle Pydantic validation errors (array of details)
    let message = `HTTP error! status: ${response.status}`;
    if (error.detail) {
      if (Array.isArray(error.detail)) {
        message = error.detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', ');
      } else {
        message = error.detail;
      }
    }
    console.error('API Error:', error);
    throw new Error(message);
  }
  
  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
}

// ============ Lists API ============

export const listsApi = {
  getAll: (mediaType) => {
    const params = mediaType ? `?media_type=${mediaType}` : '';
    return fetchApi(`/lists${params}`);
  },
  
  getById: (id) => fetchApi(`/lists/${id}`),
  
  create: (data) => fetchApi('/lists', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  update: (id, data) => fetchApi(`/lists/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  
  delete: (id) => fetchApi(`/lists/${id}`, {
    method: 'DELETE',
  }),
  
  refresh: (id) => fetchApi(`/lists/${id}/refresh`, {
    method: 'POST',
  }),
  
  preview: (data) => fetchApi('/lists/preview', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  exportJson: (id) => fetchApi(`/lists/${id}/export/json`),
  exportRadarr: (id) => fetchApi(`/lists/${id}/export/radarr`),
  exportSonarr: (id) => fetchApi(`/lists/${id}/export/sonarr`),
};

// ============ Media API ============

export const mediaApi = {
  search: (query, mediaType = 'movie', page = 1) =>
    fetchApi(`/media/search?query=${encodeURIComponent(query)}&media_type=${mediaType}&page=${page}`),
  
  trending: (mediaType = 'movie', timeWindow = 'week', page = 1) =>
    fetchApi(`/media/trending?media_type=${mediaType}&time_window=${timeWindow}&page=${page}`),
  
  popular: (mediaType = 'movie', page = 1) =>
    fetchApi(`/media/popular?media_type=${mediaType}&page=${page}`),
  
  topRated: (mediaType = 'movie', page = 1) =>
    fetchApi(`/media/top-rated?media_type=${mediaType}&page=${page}`),
  
  upcoming: (page = 1) => fetchApi(`/media/upcoming?page=${page}`),
  
  nowPlaying: (page = 1) => fetchApi(`/media/now-playing?page=${page}`),
  
  airingToday: (page = 1) => fetchApi(`/media/airing-today?page=${page}`),
  
  getDetails: (mediaType, tmdbId) => fetchApi(`/media/${mediaType}/${tmdbId}`),
  
  getGenres: (mediaType = 'movie') => fetchApi(`/media/genres/${mediaType}`),
  
  getFilters: () => fetchApi('/media/filters'),
  
  getSortOptions: () => fetchApi('/media/sort-options'),

  discover: (page = 1, filters = [], sortBy = 'popularity.desc') => {
    const filterStr = JSON.stringify(filters);
    return fetchApi(`/discover?page=${page}&sort_by=${sortBy}&filters=${encodeURIComponent(filterStr)}`);
  },
};

// ============ Image URL Helper ============

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';

export const getImageUrl = (path, size = 'w500') => {
  if (!path) return null;
  return `${TMDB_IMAGE_BASE}/${size}${path}`;
};

export const getPosterUrl = (path) => getImageUrl(path, 'w342');
export const getBackdropUrl = (path) => getImageUrl(path, 'w1280');
export const getProfileUrl = (path) => getImageUrl(path, 'w185');
