import React, { useState, useEffect } from "react";
import Chatbot from "./components/Chatbot";
import { Button } from "./components/ui/button";
import { Toggle } from "./components/ui/toggle";
import { InfoCard, InfoButton } from "./components/ui/infocard";

export default function App() {
  // use state for dark mode
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    // check for saved preference in local storage first
    const savedPreference = localStorage.getItem("darkMode");
    if (savedPreference !== null) {
      return savedPreference === "true";
    }
    // if no saved preference, use system preference
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  // state for info card visibility
  const [isInfoCardOpen, setIsInfoCardOpen] = useState<boolean>(false);

  // effect to apply dark mode class to document
  useEffect(() => {
    // toggle in one call, and persist
    document.documentElement.classList.toggle("dark", darkMode);
    // set boolean darkMode and save it
    localStorage.setItem("darkMode", JSON.stringify(darkMode));
  }, [darkMode]);

  // listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      // only update if no explicit user preference is set
      if (localStorage.getItem("darkMode") === null) {
        setDarkMode(e.matches);
      }
    };

    // add the listener
    mediaQuery.addEventListener("change", handleChange);

    // cleanup function for updates
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-gray-50 dark:bg-gray-900 transition-colors duration-500">
      {/* Header with title and dark mode toggle */}
      <header className="w-full max-w-3xl px-4 py-4 pt-8 pb-6 flex items-center justify-between">
        <h1
          style={{ fontFamily: "Figtree" }}
          className="text-4xl font-bold text-primary dark:text-primary-light transition-colors text-center"
        >
          Hoop-GPT
        </h1>

        <div className="flex items-center space-x-4">
          <InfoButton onClick={() => setIsInfoCardOpen(true)} />
          <Toggle
            enabled={darkMode}
            onChange={setDarkMode}
            label={darkMode ? "🌙" : "☀️"}
          />
        </div>
      </header>

      <div className="w-full max-w-3xl px-4 mx-auto mb-12 flex-grow">
        <p
          style={{ fontFamily: "Figtree" }}
          className="text-lg text-gray-600 dark:text-gray-300 mb-6 text-center"
        >
          Ask about NBA players, teams, stats, records, and more!
        </p>
        <Chatbot />
      </div>

      <footer
        style={{ fontFamily: "Figtree" }}
        className="w-full py-4 text-center text-sm text-gray-500 dark:text-gray-400"
      >
        © {new Date().getFullYear()} Hoop-GPT - All NBA logos and data are
        property of the NBA and its teams
      </footer>

      <InfoCard
        isOpen={isInfoCardOpen}
        onClose={() => setIsInfoCardOpen(false)}
      />
    </div>
  );
}
