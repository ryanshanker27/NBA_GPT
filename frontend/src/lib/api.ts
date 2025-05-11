import axios from "axios";

// choose API URL based on prod or dev
const isDev = import.meta.env.DEV;
const base = isDev
  ? "/api"                             
  : import.meta.env.VITE_API_URL;     

console.log("↪️  Using API base:", base);

const api = axios.create({
  baseURL: base,
  headers: { "Content-Type": "application/json" },
});

export default api;