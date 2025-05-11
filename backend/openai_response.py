from openai import OpenAI
# from config import Config
import psycopg2
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal
from user_session import UserSession
import re
import time as tm
import os

schema = """
teams (contains info on every NBA team):
- team_id (INT, PK)
- full_name (VARCHAR)
- abbreviation (VARCHAR)
- nickname (VARCHAR)
- city (VARCHAR)

players (contains info on every NBA player in the database):
- player_id (INT, PK)
- first_name (VARCHAR)
- last_name (VARCHAR)
- player_name (VARCHAR)
- height (INT, in inches)
- weight (INT, in pounds)
- position (VARCHAR ENUM: Guard, Guard-Forward, Forward, Forward-Guard, Center, Forward-Center, Center-Forward)
- school (VARCHAR) - college the player attended
- country (VARCHAR) - country of origin
- birthdate (date)
- from_year (INT) - year player entered the league
- draft_year (VARCHAR) - year player was drafted; if undrafted, this column says 'Undrafted'
- draft_round (VARCHAR) - if undrafted, this column says 'Undrafted'
- draft_number (VARCHAR) - if undrafted, this column says 'Undrafted'

games (contains info on every individual game in the database):
- game_id (INT, PK)
- game_date (date) - date of the game
- home_team (INT, FK -> teams.team_id)
- away_team (INT, FK -> teams.team_id)
- home_score (INT)
- away_score (INT)
- season_id (INT) - 22020 = 2020-21 season, 22021 = 2021-22 season, etc.
- season_type (VARCHAR ENUM: Regular Season or Playoffs)
- playoff_game_round (INT) - 0 for a regular season same, 1 for a first round playoff game, 2 for a conference semifinals playoff game, 3 for conference finals playoff game, 4 for Finals game
- playoff_game_num (INT)

game_stats_player (contains info on all player statistics from a given game):
- game_id (INT, FK -> games.game_id)
- player_id (INT, FK -> players.player_id) - id of the player who played in the given game
- team_id (INT, FK -> teams.team_id) - team the player played for in the given game
- player_name (VARCHAR -> players.player_name)
- entered_game (INT) - 1 if player entered given game, 0 if not
- min (INT) - minutes
- fgm (INT) - field goals made
- fga (INT) - field goals attempted
- fg3m (INT) - 3 pointers made
- fg3a (INT) - 3 pointers attempted
- ftm (INT) - free throws made
- fta (INT) - free throws attempted
- oreb (INT) - offensive rebounds
- reb (INT) - rebounds
- ast (INT) - assists
- stl (INT) - steals
- blk (INT) - blocks
- to (INT) - turnovers
- pts (INT) - points
- plus_minus (INT)
- off_rating (FLOAT) - offensive rating, advanced statistic
- def_rating (FLOAT) - defensive rating, advanced statistic
- oreb_pct (FLOAT) - offensive rebound percentage, advanced statistic
- reb_pct (FLOAT) - rebound percentage, advanced statistic
- efg_pct (FLOAT) - effective field goal percentage, advanced statistic
- usg_pct (FLOAT) - usage percentage, advanced statistic
- pie (FLOAT) - player impact estimate or efficiency, advanced statistic

game_stats_team (contains info on all team statistics from a given game):
- game_id (INT, FK -> games.game_id)
- team_id (INT, FK -> teams.team_id)
- min (INT) - minutes
- fgm (INT) - field goals made
- fga (INT) - field goals attempted
- fg3m (INT) - 3 pointers made
- fg3a (INT) - 3 pointers attempted
- ftm (INT) - free throws made
- fta (INT) - free throws attempted
- oreb (INT) - offensive rebounds
- reb (INT) - rebounds
- ast (INT) - assists
- stl (INT) - steals
- blk (INT) - blocks
- to (INT) - turnovers
- pts (INT) - points
- plus_minus (INT)
- off_rating (FLOAT) - offensive rating, advanced statistic
- def_rating (FLOAT) - defensive rating, advanced statistic
- oreb_pct (FLOAT) - offensive rebound percentage, advanced statistic
- reb_pct (FLOAT) - rebound percentage, advanced statistic
- efg_pct (FLOAT) - effective field goal percentage, advanced statistic
- pace (FLOAT) - pace
"""

PLAYER_AVERAGE_EXAMPLES = """
Example User Query: What did each Celtics player average over the last 20 games?
Example Output: SELECT p.player_name AS "Player Name", 
       AVG(gsp.pts) AS "PPG", 
       AVG(gsp.reb) AS "RPG", 
       AVG(gsp.ast) AS "APG", 
       AVG(gsp.min) AS "MIN", 
       AVG(gsp.stl) AS "SPG", 
       AVG(gsp.blk) AS "BPG"
FROM game_stats_player gsp
JOIN players p ON gsp.player_id = p.player_id
JOIN games g ON gsp.game_id = g.game_id
JOIN teams t ON gsp.team_id = t.team_id
WHERE t.full_name = 'Boston Celtics' AND gsp.entered_game = 1
AND g.game_id IN (SELECT game_id FROM games 
WHERE home_team = (SELECT team_id FROM teams WHERE full_name = 'Boston Celtics') OR away_team = (SELECT team_id FROM teams WHERE full_name = 'Boston Celtics') ORDER BY game_date DESC LIMIT 20)
GROUP BY p.player_name
ORDER BY "PPG" DESC;

Example User Query: Compare the averages for LeBron James, Luka Doncic and Nikola Jokic for the last 2 months, include defensive stats and shooting percentages
Example Output: SELECT p.player_name AS "Player Name", 
       COUNT(*) AS "Games Played",
       AVG(gsp.pts) AS "PPG",
       AVG(gsp.reb) AS "RPG",
       AVG(gsp.ast) AS "APG",
       AVG(gsp.stl) AS "SPG",
       AVG(gsp.blk) AS "BPG",
       SUM(NULLIF(gsp.fgm, 0.0))/SUM(NULLIF(gsp.fga, 0.0)) * 100.0 AS "FG%",
       SUM(NULLIF(gsp.fg3m, 0.0))/SUM(NULLIF(gsp.fg3a, 0.0)) * 100.0 AS "FG3%",
       SUM(NULLIF(gsp.ftm, 0.0))/SUM(NULLIF(gsp.fta, 0.0)) * 100.0 AS "FT%"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
WHERE gsp.entered_game = 1 AND g.game_date >= CURRENT_DATE - INTERVAL '2 months' AND p.player_name IN ('LeBron James', 'Luka Dončić', 'Nikola Jokić')
GROUP BY p.player_name, g.season_id
ORDER BY p.player_name;

Example User Query: How many points does Jaylen Brown average against each NBA team in the playoffs?
Example Output: SELECT CASE WHEN t1.team_id = home.team_id THEN away.full_name ELSE home.full_name END AS "Opponent",
       AVG(gsp.pts) AS "PPG",
       SUM(gsp.pts) AS "Total Points Scored",
       COUNT(gsp.game_id) AS "Games Played",
       AVG(gsp.reb) AS "RPG",
       AVG(gsp.ast) AS "APG"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN teams t1 ON gsp.team_id = t1.team_id
JOIN teams home ON g.home_team = home.team_id
JOIN teams away ON g.away_team = away.team_id
WHERE g.season_type = 'Playoffs' AND gsp.entered_game = 1 AND gsp.player_id = (SELECT player_id FROM players WHERE player_name = 'Jaylen Brown') 
GROUP BY "Opponent"
ORDER BY "PPG" DESC;

Example User Query: NBA player leaders in true shooting percentage for a season? Must be a non-center and have averaged over 20 points per game.
Example Output: SELECT p.player_name AS "Player Name", 
       p.position AS "Position",
       (g.season_id - 20000) AS "Season Year",
       SUM(gsp.pts) / NULLIF(2 * (SUM(gsp.fga) + 0.44 * SUM(gsp.fta)) , 0.0) * 100.0 AS "True Shooting %",
       SUM(gsp.pts) AS "Total Points Scored", 
       SUM(gsp.fga) AS "Total Field Goals Attempted",
       AVG(gsp.pts) AS "PPG",
       AVG(gsp.reb) AS "RPG",
       AVG(gsp.ast) AS "APG"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
WHERE p.position NOT IN ('Center-Forward', 'Forward-Center', 'Center') AND gsp.entered_game = 1
GROUP BY p.player_name, p.position, g.season_id
HAVING AVG(gsp.pts) > 20.0
ORDER BY "True Shooting %" DESC
LIMIT 10;

Example User Query: What team had the most players that shot over 38% from three this season on at least 100 attempts? Provide all teams along with their players that met the criteria.
Example Output: WITH players_38 AS (SELECT t.full_name AS team, 
       p.player_name AS player,
       SUM(NULLIF(gsp.fg3m, 0.0))/SUM(NULLIF(gsp.fg3a, 0.0)) * 100.0 AS fg3_pct,
       SUM(NULLIF(gsp.fg3m, 0.0)) AS fg3m,
       SUM(NULLIF(gsp.fg3a, 0.0)) AS fg3a
FROM game_stats_player gsp
JOIN games g ON g.game_id = gsp.game_id
JOIN teams t ON gsp.team_id = t.team_id
JOIN players p ON gsp.player_id = p.player_id
WHERE g.season_id = 22024
GROUP BY (p.player_name, t.full_name)
HAVING SUM(NULLIF(gsp.fg3m, 0.0))/SUM(NULLIF(gsp.fg3a, 0.0)) * 100.0 > 38
ORDER BY fg3_pct DESC)
SELECT
  team AS "Team",
  COUNT(*) AS "Number of Players",
  STRING_AGG(
    player,
    ', ' ORDER BY fg3_pct DESC
  ) AS "List of Players"
FROM players_38
WHERE fg3a > 100
GROUP BY team
ORDER BY "Number of Players" DESC;

Example User Query: Compare the stats of Jayson Tatum in his wins and losses this season.
Example Output: SELECT 
    CASE WHEN (g.home_team = t.team_id AND g.home_score > g.away_score) OR (g.away_team = t.team_id AND g.away_score > g.home_score) THEN 'Win' ELSE 'Loss' END AS "Win/Loss",
    AVG(gsp.pts) AS "PPG",
    AVG(gsp.reb) AS "RPG",
    AVG(gsp.ast) AS "APG"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
JOIN teams t ON gsp.team_id = t.team_id
WHERE p.player_name = 'Jayson Tatum' AND gsp.entered_game = 1
AND g.season_id = 22024
GROUP BY "Win/Loss"
ORDER BY "Win/Loss";
"""

TEAM_PERFORMANCE_EXAMPLES = """
Example User Query: Get the results of the last 10 Cavaliers games.
Example Output: SELECT g.game_date AS "Game Date", t1.full_name AS "Home Team", g.home_score AS "Home Score", t2.full_name AS "Away Team", g.away_score AS "Away Score"
FROM games g
JOIN teams t1 ON g.home_team = t1.team_id
JOIN teams t2 ON g.away_team = t2.team_id
WHERE (t1.full_name = 'Cleveland Cavaliers' OR t2.full_name = 'Cleveland Cavaliers')
ORDER BY g.game_date DESC
LIMIT 10;

Example User Query: How many threes did the Nuggets make in their 2023 and 2024 playoff games?
Example Output: SELECT g.game_date AS "Game Date", 
       g.season_id - 20000 AS "Season",
       t1.full_name AS "Home Team", 
       t2.full_name AS "Away Team", 
       SUM(gst.fg3m) AS "Threes Made"
FROM game_stats_team gst
JOIN games g ON gst.game_id = g.game_id
JOIN teams t1 ON g.home_team = t1.team_id
JOIN teams t2 ON g.away_team = t2.team_id
WHERE gst.team_id = (SELECT team_id FROM teams WHERE full_name = 'Denver Nuggets') 
AND EXTRACT(YEAR FROM g.game_date) IN (2023, 2024)
AND g.season_type = 'Playoffs'
GROUP BY g.game_date, t1.full_name, t2.full_name, g.season_id
ORDER BY g.game_date;

Example User Query: What is the largest margin of victory for a team in the last 3 seasons?
Example Output: SELECT
  CASE
    WHEN g.home_score > g.away_score THEN home.full_name
    ELSE away.full_name
  END AS "Team",
  CASE
    WHEN g.home_score < g.away_score THEN home.full_name
    ELSE away.full_name
  END AS "Opponent",
  g.game_date AS "Game Date",
  ABS(g.home_score - g.away_score) AS "Margin of Victory"
FROM games g
JOIN teams home
  ON g.home_team = home.team_id
JOIN teams away
  ON g.away_team = away.team_id
WHERE g.season_id IN (22022, 22023, 22024)
ORDER BY "Margin of Victory" DESC
LIMIT 10;

Example User Query: What were the scores of the times the Celtics and Knicks played in the 2024-25 season?
Example Output: SELECT g.game_date AS "Game Date", t1.full_name AS "Home Team", g.home_score AS "Home Score", t2.full_name AS "Away Team", g.away_score AS "Away Score"
FROM games g
JOIN teams t1 ON g.home_team = t1.team_id
JOIN teams t2 ON g.away_team = t2.team_id
WHERE ((t1.full_name = 'Boston Celtics' AND t2.full_name = 'New York Knicks') 
   OR (t1.full_name = 'Cleveland Cavaliers' AND t2.full_name = 'Boston Celtics'))
   AND g.season_id = 22024
ORDER BY g.game_date DESC;

Example User Query: What is each NBA team's record and win percentage when they hold their opponent to less than 40% field goal percentage?
Example Output: SELECT
  t.full_name AS "Team",
  SUM(CASE WHEN ts.plus_minus > 0 THEN 1 ELSE 0 END) AS "Wins",
  SUM(CASE WHEN ts.plus_minus < 0 THEN 1 ELSE 0 END) AS "Losses",
  SUM(CASE WHEN ts.plus_minus > 0.0 THEN 1.0 ELSE 0.0 END)/COUNT(*) AS "Win Percentage"
FROM game_stats_team ts
JOIN game_stats_team os
  ON ts.game_id = os.game_id
  AND ts.team_id <> os.team_id
JOIN teams t
  ON ts.team_id = t.team_id
WHERE os.fgm / NULLIF(os.fga,0.0) < 0.40
GROUP BY t.full_name
ORDER BY "Win Percentage" DESC;
"""

PLAYER_PERFORMANCE_EXAMPLES = """
Example User Query: Get all players who last scored at least 30 points against the Los Angeles Lakers in the year 2025.
Example Output: SELECT p.player_name AS "Player Name", g.game_date AS "Game Date", t1.full_name AS "Home Team", t2.full_name AS "Away Team", gsp.pts AS "PTS", gsp.reb AS "REB", gsp.ast AS "AST", gsp.stl AS "STL", gsp.blk AS "BLK"
FROM game_stats_player gsp 
JOIN games g ON gsp.game_id = g.game_id 
JOIN teams t1 ON g.home_team = t1.team_id 
JOIN teams t2 ON g.away_team = t2.team_id 
JOIN players p ON gsp.player_id = p.player_id 
WHERE gsp.pts >= 50 AND (t1.full_name = 'Los Angeles Lakers' OR t2.full_name = 'Los Angeles Lakers') 
AND g.game_date >= '2025-01-01' AND g.game_date < '2026-01-01' 
AND gsp.team_id != (SELECT team_id FROM teams WHERE full_name = 'Los Angeles Lakers')
ORDER BY g.game_date DESC;

Example User Query: What are the most stocks recorded by a player in a single game in a second round game?
Example Output: SELECT p.player_name AS "Player Name", 
       g.game_date AS "Game Date", 
       home.full_name AS "Home Team",
       away.full_name AS "Away Team",
       gsp.stl AS "STL", 
       gsp.blk AS "BLK", 
       (gsp.stl + gsp.blk) AS "Stocks",
       gsp.pts AS "PTS",
       gsp.reb AS "REB",
       gsp.ast AS "AST"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
JOIN teams home ON g.home_team = home.team_id
JOIN teams away ON g.away_team = away.team_id
WHERE g.season_type = 'Playoffs' AND g.playoff_game_round = 2
ORDER BY "Stocks" DESC
LIMIT 10;

Example User Query: What player has the most games of over 20 shots and less than 40% field goal percentage?
Example Output: SELECT p.player_name AS "Player Name", 
       COUNT(gsp.game_id) AS "Games Count"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
WHERE gsp.fga > 20 AND (gsp.fgm::FLOAT / NULLIF(gsp.fga, 0.0)) < 0.40
GROUP BY p.player_name
ORDER BY "Games Count" DESC
LIMIT 10;

Example User Query: What team had the most players to score at least 30 points in a game this season? Rank each team and list the players that scored at least 30 points.
Example Output: SELECT t.full_name AS "Team Name", 
       COUNT(DISTINCT gsp.player_id) AS "Players Scoring At Least 30 Points",
       STRING_AGG(
    DISTINCT p.player_name,
    ', ') AS "List of Players"
FROM game_stats_player gsp
JOIN games g ON gsp.game_id = g.game_id
JOIN players p ON gsp.player_id = p.player_id
JOIN teams t ON gsp.team_id = t.team_id
WHERE g.season_id = 22024 AND gsp.pts >= 30
GROUP BY t.full_name
ORDER BY "Players Scoring At Least 30 Points" DESC
LIMIT 10;

Example User Query: Sort Kentucky, Duke, North Carolina, Kansas, and Villanova by the highest number of points a player who attended that school scored this season.
Example Output: WITH ranked AS (
  SELECT
    p.player_name      AS "Player Name",
    (g.season_id - 20000) AS "Season Year",
    g.game_date        AS "Game Date",
    home.full_name     AS "Home Team",
    away.full_name     AS "Away Team",
    gsp.pts            AS "Points Scored",
    p.school           AS "School",
    ROW_NUMBER() OVER (
      PARTITION BY p.school
      ORDER BY gsp.pts DESC
    ) AS rn
  FROM game_stats_player gsp
  JOIN games   g    ON gsp.game_id   = g.game_id
  JOIN players p    ON gsp.player_id = p.player_id
  JOIN teams   home ON home.team_id  = g.home_team
  JOIN teams   away ON away.team_id  = g.away_team
  WHERE p.school IN (
      'Kentucky','Duke','North Carolina','Kansas','Villanova'
    )
    AND g.season_id = 22024
)
SELECT "Player Name", "Season Year", "Game Date", "Home Team", "Away Team", "Points Scored", "School"
FROM ranked
WHERE rn = 1
ORDER BY "Points Scored" DESC;

Example User Query: What is the most number of points, rebounds, and assists that Jaylen Brown has had against each NBA team?
Example Output: SELECT
  opp.full_name               AS "Opponent",
  MAX(gsp.pts)                AS "Max Points",
  MAX(gsp.reb)                AS "Max Rebounds",
  MAX(gsp.ast)                AS "Max Assists"
FROM game_stats_player gsp
JOIN players p
  ON gsp.player_id = p.player_id
JOIN games g
  ON gsp.game_id   = g.game_id
JOIN teams opp
  ON opp.team_id = CASE
       WHEN gsp.team_id = g.home_team THEN g.away_team
       ELSE g.home_team
     END
WHERE p.player_name = 'Jaylen Brown'
GROUP BY opp.full_name
ORDER BY opp.full_name;
"""

PLAYER_INFORMATION_EXAMPLES = """
Example User Query: Who is the highest draft pick to ever play for the Minnesota Timberwolves?
Example Output: SELECT
  p.player_name AS "Player",
  p.draft_year AS "Draft Year",
  CAST(p.draft_round AS INT)  AS "Round",
  CAST(p.draft_number AS INT) AS "Pick In Round"
FROM players p
JOIN game_stats_player gsp 
  ON p.player_id = gsp.player_id
JOIN games g 
  ON gsp.game_id   = g.game_id
JOIN teams t 
  ON gsp.team_id   = t.team_id
WHERE
  t.full_name = 'Minnesota Timberwolves'
  AND p.draft_number <> 'Undrafted'
GROUP BY
  p.player_name, p.draft_year, p.draft_round, p.draft_number
ORDER BY
  CAST(p.draft_round  AS INT)    ASC,
  CAST(p.draft_number AS INT)    ASC
LIMIT 10;

Example User Query: What is the average height of the current San Antonio Spurs?
Example Output: SELECT AVG(p.height) AS "Average Height (inches)"
FROM players p
WHERE p.player_id IN (
  SELECT DISTINCT gsp.player_id
  FROM game_stats_player gsp
  JOIN games g 
    ON gsp.game_id = g.game_id
  WHERE 
    gsp.team_id = (
      SELECT team_id 
      FROM teams 
      WHERE full_name = 'San Antonio Spurs'
    )
    AND g.season_id = 22024
);

Example User Query: What college has the most NBA players that averaged at least 10 points in a game in a season? Return the players for each school.
Example Output: WITH season_avg AS (
  SELECT
    p.player_name,
    p.school,
    g.season_id,
    AVG(gsp.pts) AS avg_ppg
  FROM game_stats_player gsp
  JOIN players p
    ON gsp.player_id = p.player_id
  JOIN games g
    ON gsp.game_id   = g.game_id
  WHERE gsp.entered_game = 1
  GROUP BY
    p.player_id,
    p.player_name,
    p.school,
    g.season_id
),
qualified_players AS (
  SELECT DISTINCT
    player_name,
    school
  FROM season_avg
  WHERE avg_ppg >= 20
)
SELECT
  school            AS "College",
  COUNT(*)          AS "Num Players ≥10 PPG",
  STRING_AGG(
    DISTINCT player_name,
    ', ') AS "List of Players"
FROM qualified_players
GROUP BY school
ORDER BY COUNT(*) DESC
LIMIT 10;

Example User Query: What country had the most NBA players to play a game in the 2024-25 season?
Example Output: SELECT p.country AS "Country", 
       COUNT(DISTINCT p.player_id) AS "Number of Players"
FROM players p
JOIN game_stats_player gsp ON p.player_id = gsp.player_id
JOIN games g ON gsp.game_id = g.game_id
WHERE g.season_id = 22024 AND gsp.entered_game = 1
GROUP BY p.country
ORDER BY "Number of Players" DESC
LIMIT 10;
"""

TEAM_AVERAGES_EXAMPLES = """
Example User Query: What is the average number of points scored and opponent points scored per game for each team in the 2024-25 playoffs?
Example Output: SELECT
  t.full_name AS "Team",
  AVG(gst.pts) AS "Avg Points Scored",
  AVG(
    CASE
      WHEN g.home_team = gst.team_id THEN g.away_score
      ELSE g.home_score
    END
  ) AS "Avg Opponent Points"
FROM game_stats_team gst
JOIN games g ON gst.game_id = g.game_id
JOIN teams t ON gst.team_id = t.team_id
WHERE g.season_id   = 22024
  AND g.season_type = 'Playoffs'
GROUP BY t.full_name
ORDER BY "Avg Points Scored" DESC;

Example User Query: What are the three point shooting statistics per game of every team in the 2023 season?
Example Output: SELECT t.full_name AS "Team", 
       AVG(gst.fg3m) AS "Three Pointers Made", 
       AVG(gst.fg3a) AS "Three Pointers Attempted", 
       (SUM(gst.fg3m) * 100.0 / NULLIF(SUM(gst.fg3a), 0)) AS "FG3%"
FROM game_stats_team gst
JOIN games g ON gst.game_id = g.game_id
JOIN teams t ON gst.team_id = t.team_id
WHERE g.season_id = 22023
GROUP BY t.full_name
ORDER BY "FG3%" DESC;

Example User Query: Compare every NBA team's points scored per game in wins vs points scored per game in losses in the 2024-25 season.
Example Output: SELECT t.full_name AS "Team", 
       AVG(CASE WHEN g.home_team = gst.team_id AND g.home_score > g.away_score THEN gst.pts 
                WHEN g.away_team = gst.team_id AND g.home_score <= g.away_score THEN gst.pts
                END) AS "Points Scored Per Game in Wins", 
       AVG(CASE WHEN g.away_team = gst.team_id AND g.home_score > g.away_score THEN gst.pts
                WHEN g.home_team = gst.team_id AND g.home_score < g.away_score THEN gst.pts 
                END) AS "Points Scored Per Game in Losses"
FROM game_stats_team gst
JOIN games g ON gst.game_id = g.game_id
JOIN teams t ON gst.team_id = t.team_id
WHERE g.season_id = 22024
GROUP BY t.full_name
ORDER BY t.full_name;

Example User Query: What is the net rating of the Boston Celtics against all other NBA teams?
Example Output: SELECT CASE WHEN t1.team_id = home.team_id THEN away.full_name ELSE home.full_name END AS "Opponent",
       AVG(gst.off_rating) AS "Offensive Rating",
       AVG(gst.def_rating) AS "Defensive Rating",
       AVG(gst.off_rating) - AVG(gst.def_rating) AS "Net Rating"
FROM game_stats_team gst
JOIN games g ON gst.game_id = g.game_id
JOIN teams t1 ON gst.team_id = t1.team_id
JOIN teams home ON g.home_team = home.team_id
JOIN teams away ON g.away_team = away.team_id
WHERE gst.team_id = (SELECT team_id FROM teams WHERE full_name = 'Boston Celtics') 
GROUP BY "Opponent"
ORDER BY "Net Rating" DESC;
"""

QUERY_BREAKDOWN_TEMPLATE = """
Please break down this NBA query into bullets of:
- Query type (one of either Single Game Player Performance, Single Game Team Performance, Multi-Game Player Performance, Multi-Game Team Performance, or Player Information)
    - Put double dollar signs around the query type.
    - Averages or aggregate statistics over a period of time are always multi-game queries.
    - Questions that return performances from specific games are always single game queries.
- Key entities (players, teams, dates, stats, etc.)
    - If the query is asking about a player, include the player's full name with triple asterisks around the name.
    - Return the full team name in the breakdown (e.g. "Boston Celtics").
- Filters/conditions (e.g. "pts ≥ 30", seasons, age at game date)
- Output variables (e.g. game_date, home_team, away_team, pts, reb, ast, …)
    - Include game date and both team names any row that corresponds to a specific game.
- Calculation components and variables (if any calculations are performed)

The previous chat history will be provided for more context, though it may not always be relevant to the new query.
If the chat history is not relevant, do not alter the given query.

Chat history: {chat_history}

Query: {query}
"""

SQL_PROMPT_TEMPLATE = """

Given:
• A user query  
• Its breakdown (bdq)  
• The NBA schema below and 

Generate a PostgreSQL statement that:

Join tables: games, game_stats_*, teams, players; apply breakdown filters.

Required fields:
- Game rows: game_date, home_team.full_name AS "HOME_TEAM", away_team.full_name AS "AWAY_TEAM", home_score AS "HOME_SCORE", away_score AS "AWAY_SCORE".
- Player performance: MIN AS "MIN", PTS AS "PTS", REB AS "REB", AST AS "AST", STL AS "STL", BLK AS "BLK".
- Player averages: PPG AS "PPG", RPG AS "RPG", APG AS "APG".
- Include any extra fields used for filtering or calculations.

Global rules:
1. Use full team names.
2. Cast divisions/percentages/averages to FLOAT; multiply percentages by 100.
3. Season = season_id - 20000 (e.g. 22024 → 2024-25); assume calendar year if only year given.
4. AGE calculated at game_date.
5. LIMIT ≤ 30 rows (≤ 10 if superlative: most/best/highest/least/lowest/leading).
6. Alias non-name/date/rating columns as UPPER-CASE abbreviations in quotes (e.g. "PTS", "FG3%", "USG%"); leave names/dates/ratings unaliased.

Opponent-specific filtering:
- For Team A vs Team B:  
  WHERE (home_team=Team A AND away_team=Team B) OR (away_team=Team A AND home_team=Team B).  
  Define subject_score = home_score if Team A is home (else away_score), opponent_score likewise; derive W/L by comparison.
- Exclude Team B's team/player stats; only return Team A's.
- For player-vs-team queries, omit players from that team.
- For averages vs multiple opponents, GROUP BY opponent.

Only output the SQL. No extra text.

Examples: {examples}

Schema: {schema}

Query Breakdown: {bdq}

User Query:
"""

RESPONSE_TEMPLATE = """
    Analyze the following data table and provide a brief answer to the user's query.
    
    Query: {query}
    
    Data:
    {raw_table}
    
    Provide ONLY a brief (2-3 sentences) conversational summary that directly answers the query.
    Do not include the table or any markdown formatting in your response.
    Present only the facts in a neutral tone without excessive adjectives.
    """

ERROR_TEMPLATE = """
    Based on the user's query and the error that occurred, provide a helpful response.
    
    Query: {query}
    
    Error: {error}
    
    Provide a friendly response explaining the issue in simple terms and asking the user to reword their question.
    Don't include technical details about SQL errors, but suggest what specific information they might provide to clarify their question.
    """

_openai_client = None

def get_openai_client():
    """Get or create an OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    return _openai_client

def call_openai_with_retry(model, messages, max_tokens = 1000, temperature = 0.1, top_p = 0.95, retries=3, backoff=2):
    client = get_openai_client()
    last_error = None
    
    for attempt in range(retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
        except Exception as e:
            last_error = e
            # If not the last attempt, wait and retry
            if attempt < retries - 1:
                tm.sleep(backoff ** attempt)
    
    # If we get here, all attempts failed
    # Re-raise the last error
    raise last_error

def break_down_query(query, user_session: UserSession):
    chat_history = ""
    if user_session.messages:
        chat_history = "\n".join(user_session.messages[-4:])
    prompt = QUERY_BREAKDOWN_TEMPLATE.format(chat_history = chat_history, query = query)
    print("Query Breakdown Prompt:", prompt)
    messages = [
        {"role": "system", "content": "You are an assistant that extracts essential components from NBA queries for SQL generation."},
        {"role": "user", "content": prompt},
    ]

    response = call_openai_with_retry(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=400,
        temperature=0.2,
        top_p=0.95
    )
    querybreakdown = response.choices[0].message.content.strip()
    print("Query Breakdown:", querybreakdown)
    return querybreakdown

def get_sql_query(query, querybreakdown):
    match = re.search(r"\$\$(.*?)\$\$", querybreakdown)
    querytype = match.group(1).lower() if match else None

    if querytype == "single game player performance":
        examples = PLAYER_PERFORMANCE_EXAMPLES
    elif querytype == "single game team performance":
        examples = TEAM_PERFORMANCE_EXAMPLES
    elif querytype == "multi-game player performance":
        examples = PLAYER_AVERAGE_EXAMPLES
    elif querytype == "multi-game team performance":
        examples = TEAM_AVERAGES_EXAMPLES
    elif querytype == "player information":
        examples = PLAYER_INFORMATION_EXAMPLES
    else:
        examples = PLAYER_AVERAGE_EXAMPLES

    messages = [
        {"role": "system", "content": f"You are a SQL query generator for NBA statistics. {SQL_PROMPT_TEMPLATE.format(bdq = querybreakdown, schema = schema, examples = examples)}"},
        {"role": "user", "content": query},
    ]

    response = call_openai_with_retry(
        model="gpt-4.1-mini",
        messages = messages,
        max_tokens=1000,
        temperature=0.0,
        top_p=0.7
    )

    sqlquery = response.choices[0].message.content.strip()
    if sqlquery.lstrip().startswith("```sql"):
        # Remove the ```sql marker
        sqlquery = re.sub(r"^```sql\s*\n?", "", sqlquery, flags=re.IGNORECASE)
        # Remove a trailing ``` if present
        sqlquery = re.sub(r"\n?```$", "", sqlquery)
    print("SQL Query:", sqlquery)
    # Check for unsupported responses
    if "I cannot answer" in sqlquery or "cannot be answered" in sqlquery or not sqlquery.strip().lower().startswith("select"):
        return None
    return sqlquery

def format_table_data(columns: List[str], rows: List[Tuple]) -> str:
    """Format data as a nicely formatted table with proper column headers"""
    # Clean and format column names
    formatted_columns = [col.replace('_', ' ') for col in columns]
    
    # Process rows to round decimal values
    processed_rows = []
    for row in rows:
        processed_row = []
        for val in row:
            # Check if the value is a float and round it
            if isinstance(val, (float, Decimal)):
                processed_row.append(f"{val:.2f}")
            else:
                processed_row.append(str(val))
        processed_rows.append(tuple(processed_row))

    print(processed_rows)
    
    # Determine column widths
    col_widths = []
    for i in range(len(formatted_columns)):
        col_values = [str(row[i]) for row in processed_rows]
        col_values.append(formatted_columns[i])
        col_widths.append(max(len(val) for val in col_values) + 2)  # +2 for padding
    
    # Create header
    header = "| " + " | ".join(f"{formatted_columns[i]:<{col_widths[i]}}" for i in range(len(formatted_columns))) + " |"
    separator = "|-" + "-|-".join("-" * width for width in col_widths) + "-|"
    
    # Create rows
    formatted_rows = []
    for row in processed_rows:
        formatted_row = "| " + " | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(formatted_columns))) + " |"
        formatted_rows.append(formatted_row)
    
    return f"{header}\n{separator}\n" + "\n".join(formatted_rows)

def get_response(query, columns, rows):
    formatted_table = format_table_data(columns, rows)
    print(formatted_table)
    raw_table = "| " + " | ".join(columns) + " |\n"
    raw_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"
    for row in rows:
        raw_table += "| " + " | ".join(str(item) for item in row) + " |\n"
    
    prompt = RESPONSE_TEMPLATE.format(query = query, raw_table = raw_table)
    response = call_openai_with_retry(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains data in a human-friendly way."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200
        )
    llm_response = response.choices[0].message.content.strip()
    print(llm_response)
    return formatted_table, llm_response

def get_error_response(query, error):
    prompt = ERROR_TEMPLATE.format(query=query, error=error)
    response = call_openai_with_retry(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains database errors in simple terms."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )
    error_response = response.choices[0].message.content.strip()
    return error_response