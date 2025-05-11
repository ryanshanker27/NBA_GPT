import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "./card";
import { Button } from "./button";

interface InfoCardProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InfoCard({ isOpen, onClose }: InfoCardProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        modalRef.current &&
        !modalRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscapeKey);
    }

    return () => {
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center p-8 z-50 bg-black/50 transition-opacity overflow-y-auto pt-16 flex-col h-[80vh]">
      <div
        ref={modalRef}
        className="w-full max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl animate-in fade-in duration-300"
      >
        <Card
          className="w-full animate-in fade-in duration-300"
          style={{
            justifySelf: "center",
            alignSelf: "center",
          }}
        >
          <CardContent className="p-4 md:p-6">
            <div className="flex justify-between items-center mb-6">
              <h2
                style={{
                  fontFamily: "Figtree",
                  paddingLeft: "25px",
                  paddingTop: "10px",
                }}
                className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-gray-100"
              >
                About Hoop-GPT
              </h2>
              <Button
                onClick={onClose}
                className="h-8 w-8 p-0 flex items-center justify-center rounded-full"
                style={{ marginRight: "25px", marginTop: "10px" }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </Button>
            </div>

            <div
              className="space-y-4 text-gray-700 dark:text-gray-300"
              style={{
                paddingLeft: "25px",
                paddingRight: "25px",
                paddingTop: "10px",
              }}
            >
              <p style={{ fontFamily: "Figtree" }}>
                Hoop-GPT is an interactive tool that allows you to query NBA
                statistics through natural language. Ask questions about
                players, teams, standings, historical records, and more.
              </p>

              <h3
                style={{ fontFamily: "Figtree" }}
                className="text-xl md:text-2xl font-semibold text-gray-800 dark:text-gray-100"
              >
                How to Use
              </h3>
              <p style={{ fontFamily: "Figtree" }}>
                Simply type your question in the chat box and press the send
                button. The chatbot will analyze your query and return relevant
                NBA statistics, often with formatted tables for better
                readability.
              </p>

              <h3
                style={{ fontFamily: "Figtree" }}
                className="text-xl md:text-2xl font-semibold text-gray-800 dark:text-gray-100 mt-6 mb-3"
              >
                Example Questions
              </h3>
              <ul className="list-disc pl-5 space-y-1">
                <li>Who led the NBA in points per game in 2024-25?</li>
                <li>
                  Get the results of the last 10 games between the Celtics and
                  Heat.
                </li>
                <li>
                  How many points did Jayson Tatum average in the last 5 games?
                </li>
                <li>Which team had the best defensive rating in 2023?</li>
              </ul>

              <p className="text-md text-gray-500 dark:text-gray-400 mt-6">
                This project uses NBA data to provide insights and statistics.
                All NBA logos, player information, and related data are property
                of the NBA and its teams. This project only uses data after the
                2020-21 season.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function InfoButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-white hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors"
      style={{ marginRight: "10px", width: "48px", height: "36px" }}
      aria-label="Information"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
    </button>
  );
}
