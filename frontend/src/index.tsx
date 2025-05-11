import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

console.log("Starting app; API_BASE =", import.meta.env.VITE_API_URL);
const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
