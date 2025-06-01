import React, { useState, useRef, useEffect } from "react";
import api from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Input } from "./ui/input";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";

// define message shape
interface Message {
  // type can be user query or bot response
  type: "query" | "response";
  content: string;
  // optionally can have a table or error message
  table?: string;
  error?: boolean;
}

export default function Chatbot() {
  // query holds user text, default empty string
  const [query, setQuery] = useState("");
  // boolean for waiting for response, default false
  const [loading, setLoading] = useState(false);
  // array of chat bubbles
  const [messages, setMessages] = useState<Message[]>([]);
  // reference to a div element at the bottom of the chat
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // New states for text animation
  const [animatingMessageIndex, setAnimatingMessageIndex] = useState<
    number | null
  >(null);
  const [displayedContent, setDisplayedContent] = useState<string>("");

  // allows for autoscrolling to the chat bottom or most recent messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // watch messages, run scroll to bottom when messages updates
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // New function for text animation
  const animateTyping = (
    fullText: string,
    currentIndex: number,
    messageIndex: number
  ) => {
    if (currentIndex <= fullText.length) {
      setDisplayedContent(fullText.substring(0, currentIndex));
      setTimeout(() => {
        animateTyping(fullText, currentIndex + 1, messageIndex);
      }, 40); // Adjust speed as needed
    } else {
      setAnimatingMessageIndex(null);
    }
  };

  // form submission
  const handleSubmit = async (e: React.FormEvent) => {
    // do not reload page
    e.preventDefault();
    if (!query.trim()) return;

    // add user query to messages, set loading to true
    setMessages((prev) => [...prev, { type: "query", content: query }]);
    setLoading(true);

    try {
      // send query to backend
      const res = await api.post("/query", { query });

      if (res.data.success) {
        // if successful, create new messages array with the response
        const newMessages = [
          ...messages,
          { type: "query", content: query },
          {
            type: "response",
            content: res.data.response, // summary text
            table: res.data.table, // markdown table
            error: false,
          },
        ];

        // Start animating the new message
        const newMessageIndex = newMessages.length - 1;
        setAnimatingMessageIndex(newMessageIndex);
        setDisplayedContent("");
        animateTyping(res.data.response, 0, newMessageIndex);

        // Update messages state
        setMessages((prev) => [
          ...prev,
          {
            type: "response",
            content: res.data.response, // summary text
            table: res.data.table, // markdown table
            error: false,
          },
        ]);
      } else {
        // show error text if unsuccessful
        setMessages((prev) => [
          ...prev,
          {
            type: "response",
            content:
              res.data.response ||
              "Sorry, I couldn't process your request. Please try rewording your question.",
            error: true,
          },
        ]);
      }

      // clear input box
      setQuery("");
    } catch (error) {
      // if an error arises with the network or database, show a different response
      console.error("Error fetching response:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "response",
          content:
            "Sorry, I couldn't connect to the database. Please try again later.",
          error: true,
        },
      ]);
    } finally {
      // undo loading spinner
      setLoading(false);
    }
  };

  return (
    // column flex container at 70% of viewport height
    <div className="flex flex-col h-[70vh]">
      {/* card to fill parent, hide overflowing content, round corners */}
      <Card className="flex-grow overflow-hidden flex flex-col rounded-3full">
        {/* remove padding and fill card */}
        <CardContent className="p-0 flex flex-col h-full">
          {/* Messages area */}
          {/* scroll vertically if overflows */}
          <div className="flex-grow overflow-y-auto p-6 space-y-6">
            {/* map messages to chat bubbles */}
            {/* if no messages, show welcome message */}
            {messages.length === 0 ? (
              // full height, center text and items,
              <div className="h-full flex items-center justify-center text-center">
                <div className="max-w-md">
                  <h3
                    style={{ fontFamily: "Figtree" }}
                    className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-200"
                  >
                    Welcome to Hoop-GPT!
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Ask questions about NBA players, teams, stats, records, and
                    more!
                  </p>
                </div>
              </div>
            ) : (
              // if messages is not empty
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    // push right if user query, push left if response
                    message.type === "query" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    // Updated styling for message bubbles
                    className={`max-w-[80%] ${
                      // CHANGE: Updated styles for user messages to center text vertically
                      message.type === "query"
                        ? "bg-primary text-white rounded-full flex items-center justify-center py-2 px-4"
                        : message.error
                        ? "bg-red-50 dark:bg-red-900/20 text-gray-800 dark:text-gray-200 rounded-3xl px-4 py-3"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-3xl px-4 py-3"
                    }`}
                  >
                    {/* Display message content with animation for responses */}
                    <p className="whitespace-pre-wrap my-1">
                      {message.type === "response" &&
                      index === animatingMessageIndex
                        ? displayedContent
                        : message.content}
                    </p>

                    {/* Render table if it exists and this isn't an error message */}
                    {message.table &&
                      !message.error &&
                      message.table.trim() && (
                        <div className="mt-4 bg-white dark:bg-gray-800 rounded-3xl p-2 border border-gray-200 dark:border-gray-600 max-w-full">
                          <div className="overflow-x-auto">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                table: (props) => (
                                  <table
                                    {...props}
                                    className="min-w-full border-collapse text-sm table-fixed"
                                  />
                                ),
                                thead: (props) => (
                                  <thead
                                    {...props}
                                    className="bg-gray-50 dark:bg-gray-900"
                                  />
                                ),
                                th: (props) => (
                                  <th
                                    {...props}
                                    className="px-3 py-2 text-center font-semibold text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700"
                                  />
                                ),
                                tbody: (props) => (
                                  <tbody
                                    {...props}
                                    className="divide-y divide-gray-200 dark:divide-gray-700"
                                  />
                                ),
                                td: (props) => (
                                  <td
                                    {...props}
                                    className="px-3 py-2 text-center text-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
                                  />
                                ),
                              }}
                            >
                              {message.table}
                            </ReactMarkdown>
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
            {/* CHANGE: Added items-center for vertical alignment */}
            <form
              onSubmit={handleSubmit}
              className="flex items-center space-x-8"
            >
              {/* text type, controls/updates query value, prevents typing while loading response */}
              <Input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about the NBA..."
                disabled={loading}
                className="flex-grow text-base py-3 rounded-full"
              />
              {/* call handlesubmit when clicked */}
              <Button
                type="submit"
                disabled={loading}
                className="margin-left: 8px min-w-[46px] h-[46px] flex items-center justify-center rounded-full"
              >
                {/* show spinner if loading otherwise show arrow */}
                {loading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    ></path>
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-5 h-5"
                  >
                    <path d="M22 2L11 13"></path>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                  </svg>
                )}
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
