import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

// Card container: renders children inside a styled div
export function Card({ className = "", children, ...props }: CardProps) {
  return (
    <div
      style={{ fontFamily: "Figtree" }}
      className={`bg-white shadow-sm border border-gray-100 rounded-[2vw] overflow-hidden transition-colors duration-300 dark:bg-gray-800 dark:border-gray-700 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

// CardContent: inner padding for Card
export function CardContent({ className = "", children, ...props }: CardProps) {
  return (
    <div
      style={{ fontFamily: "Figtree" }}
      className={`p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
