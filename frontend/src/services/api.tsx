import axios from 'axios';

const api = axios.create({
  baseURL: '/', // Использование прокси из vite.config.ts и nginx.conf
});

// Пример функции для запроса тестового маршрута
export const getTestMessage = async () => {
  const response = await api.get('/test');
  return response.data;
};

export default api;
