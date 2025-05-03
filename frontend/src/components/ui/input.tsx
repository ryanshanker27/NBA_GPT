import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export function Input({ className = "", ...props }: InputProps) {
  return (
    <input
      className={`border border-gray-300 rounded-full px-4 py-2 w-full 
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50 focus:border-primary
        dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:focus:border-primary-light
        disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed
        placeholder:text-gray-400 dark:placeholder:text-gray-500
        transition-all duration-200 ${className}`}
      {...props}
    />
  );
}
