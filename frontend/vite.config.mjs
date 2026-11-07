// Same-origin API in development and preview; production Nginx already proxies /api.
export const apiProxy = {
  '/api': { target: process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' },
};
export default { server: { proxy: apiProxy }, preview: { proxy: apiProxy } };
