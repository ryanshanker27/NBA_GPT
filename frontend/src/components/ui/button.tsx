import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

export function Button({ className = "", children, ...props }: ButtonProps) {
  return (
    <button
      style={{ marginLeft: 8 }}
      className={`px-4 py-2 rounded-full font-medium bg-primary text-white shadow-sm
        hover:bg-primary-dark hover:shadow
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50
        dark:bg-primary-light dark:hover:bg-primary
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
        transition-all duration-200 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
