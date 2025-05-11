# Hoop-GPT
A conversational AI chatbot that utilizes the OpenAI API to deliver real-time NBA player and team performance insights by dynamically generating SQL queries against a self‑built PostgreSQL database.

## Key Features
 
- **SQL Generation & RAG Workflow**  
  1. **Query Breakdown**: Parses and structures the user’s intent.  
  2. **SQL Prompting**: Applies different prompt templates by query type to produce optimized SQL.  
  3. **Database Retrieval**: Executes the generated query on PostgreSQL database (hosted in Supabase).  
  4. **Conversational Synthesis**: Summarizes and explains the raw table output with a follow‑up prompt.
 
- **Natural Language Understanding & Prompt Engineering**  
  1. Decomposes user queries into components (input/output variables, filters, key entities, query type, calculation variables).  
  2. Incorporates chat history for enriched context and fuzzy‑matching for typo correction.  
  3. Uses tailored few‑shot examples and rule‑based templates to generate accurate SQL.
 
- **Self‑Maintained NBA Database**  
  1. Daily automated upsert of game results, and team and player stats.  
  2. Custom relational schema optimized with indexing and key relationships for fast lookup, filtering, and aggregation.
 
## Tech Stack

| Layer            | Technology              | Highlights                                                 |
|------------------|-------------------------|------------------------------------------------------------|
| **Frontend**     | React.js                | Component‑based, hooks, virtual DOM                        |
|                  | Tailwind CSS            | Utility classes, custom theming, dark mode support         |
|                  | Bootstrap               | Responsive grid, pre‑styled UI components                  |
|                  | CSS                     | Custom overrides, animations, responsive breakpoints       |
| **Backend**      | Python                  | Typed code, virtual environments, dependency management    |
|                  | Flask                   | Lightweight REST API, blueprint modularization             |
|                  | OpenAI Python SDK       | Centralized client, prompt caching, error handling         |
| **Database**     | PostgreSQL              | ACID-compliant SQL, indexing, stored procedures            |
|                  | Supabase                | Managed database creation and hosting                      |
| **DevOps**       | Heroku                  | Git-based CI/CD, dyno scaling                              |
|                  | Vercel                  | Git‑based CI/CD, serverless static hosting                 |
|                  | GitHub Actions          | Automated database updates                                 |

## Usage
Navigate to the live demo: https://nba-chatbot.vercel.app. 

Type natural‑language questions such as:
- “What was LeBron James’s PPG in the 2024 playoffs?”
- “Show me how the Nets performed against the Lakers in the 2024-25 season.”
- "Who averaged the most points of all Duke players in the 2024-25 season?"

Toggle between light/dark mode using the switch in the top‑right corner.

## Next Steps
- Add Betting Data: Integrate game lines (spreads, moneylines) and player props to allow users to ask if players/teams performed relative to their lines. 
- Extended Data Coverage: Integrate advanced metrics (advanced analytics, lineup combinations).
- User Authentication: Allow personalized query history and saved favorites.
- Caching Layer: Introduce Redis for hot‑path query caching to reduce latency and API costs.

