import pandas as pd
import numpy as np
import nba_api
from nba_api.stats.endpoints import playergamelog, teamgamelog, teamdetails, boxscoreadvancedv2, boxscoreadvancedv3, boxscoretraditionalv2
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonteamroster, commonplayoffseries, commonallplayers, playerprofilev2, scoreboardv2, leaguedashplayerstats, leaguedashteamstats, commonplayerinfo
import time
import json
import random
import datetime
import os, glob
from supabase import create_client, Client
import warnings
warnings.filterwarnings('ignore')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

TEAMIDS = [1610612737, 1610612738, 1610612739, 1610612740, 1610612741, 1610612742,
 1610612743, 1610612744, 1610612745, 1610612746, 1610612747, 1610612748,
 1610612749, 1610612750, 1610612751, 1610612752, 1610612753, 1610612754,
 1610612755, 1610612756, 1610612757, 1610612758, 1610612759, 1610612760,
 1610612761, 1610612762, 1610612763, 1610612764, 1610612765, 1610612766]

def build_players_table(teamids = TEAMIDS):
    dfs = []
    for teamid in teamids:
        for i in range(5):
            season = f'20{20 + i}-{21+i}'
            print(teamid, season)
            try:
                df = commonteamroster.CommonTeamRoster(team_id = teamid, season = season).get_data_frames()[0]
                dfs.append(df[['PLAYER_ID', 'PLAYER', 'POSITION', 'HEIGHT', 'WEIGHT', 'SCHOOL']])
            except Exception as e:
                print(f"Error retrieving data for team {teamid} season {season}: {e}")
            time.sleep(1)
    return pd.concat(dfs, ignore_index=True).drop_duplicates(subset = 'PLAYER_ID')

def format_games_table(df):
    matchup_split = df['MATCHUP'].str.split()
    df['primary_team'] = matchup_split.str[0]
    df['home_team'] = np.where(matchup_split.str[1] == 'vs.', matchup_split.str[0], matchup_split.str[2])
    df['away_team'] = np.where(matchup_split.str[1] == 'vs.', matchup_split.str[2], matchup_split.str[0])
    grouped = df.groupby(['Game_ID', 'GAME_DATE', 'home_team', 'away_team', 'SEASON_ID', 'SEASON_TYPE'], as_index = False).agg({'primary_team': lambda x: list(x),
                                                                                                    'PTS': lambda x: list(x)})
    grouped[['primary_team_0', 'primary_team_1']] = pd.DataFrame(grouped['primary_team'].tolist(), index=grouped.index)
    grouped[['PTS_0', 'PTS_1']] = pd.DataFrame(grouped['PTS'].tolist(), index=grouped.index)
    grouped['home_score'] = np.where(grouped['primary_team_0'] == grouped['home_team'], grouped['PTS_0'], grouped['PTS_1'])
    grouped['away_score'] = np.where(grouped['primary_team_0'] == grouped['home_team'], grouped['PTS_1'], grouped['PTS_0'])
    grouped['GAME_DATE'] = pd.to_datetime(grouped['GAME_DATE'].str.title())
    grouped['PLAYOFF_GAME_ROUND'] = grouped['Game_ID'].astype(str).apply(lambda x: int(x[-3]) if x[2] == '4' else 0)
    grouped['PLAYOFF_GAME_NUM'] = grouped['Game_ID'].astype(str).apply(lambda x: int(x[-1]) if x[2] == '4' else 0)
    return grouped.drop(columns = ['PTS', 'primary_team', 'primary_team_0', 'primary_team_1', 'PTS_0', 'PTS_1'])

def format_games_update(df):
    grouped = df.groupby(['GAME_ID', 'GAME_DATE_EST'], as_index = False).agg({'TEAM_ID': lambda x: list(x), 'PTS': lambda x: list(x)})
    grouped[['away_team', 'home_team']] = pd.DataFrame(grouped['TEAM_ID'].tolist(), index=grouped.index)
    grouped[['away_score', 'home_score']] = pd.DataFrame(grouped['PTS'].tolist(), index=grouped.index)
    grouped['GAME_DATE'] = grouped['GAME_DATE_EST'].apply(lambda x: datetime.datetime.fromisoformat(x).date())
    grouped = grouped.drop(['TEAM_ID', 'PTS', 'GAME_DATE_EST'], axis = 1)
    grouped['SEASON_TYPE'] = grouped['GAME_ID'].astype(str).apply(lambda x: 'Regular Season' if x[2] == '2' else 'Playoffs')
    grouped['SEASON_ID'] = grouped['GAME_DATE'].apply(lambda x: x.year + 20000 if x.month >= 10 else (x.year + 19999))
    grouped['PLAYOFF_GAME_ROUND'] = grouped['GAME_ID'].astype(str).apply(lambda x: int(x[-3]) if x[2] == '4' else 0)
    grouped['PLAYOFF_GAME_NUM'] = grouped['GAME_ID'].astype(str).apply(lambda x: int(x[-1]) if x[2] == '4' else 0)
    return grouped

def update_games_table(start_date):
    today = datetime.date.today()
    current_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    dfs = []
    while current_date <= today:
        try:
            df = scoreboardv2.ScoreboardV2(game_date=current_date).get_data_frames()[1]
            df = format_games_update(df)
            dfs.append(df)
        except Exception as e:
            print(f"Error on {current_date}: {e}")
        current_date += datetime.timedelta(days=1)
        time.sleep(2)
    return pd.concat(dfs, ignore_index=True).rename(columns={'GAME_ID': 'Game_ID'})

def fetch_game_stats_tables(game_id):
    try: 
        bs_traditional = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id).get_data_frames()
        df_traditional_player = bs_traditional[0][['GAME_ID', 'TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME', 'MIN', 'FGM', 'FGA', 'FG3M', 'FG3A',
                'FTM', 'FTA', 'OREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS', 'PLUS_MINUS']]
        print('Before')
        df_traditional_player['MIN'] = df_traditional_player['MIN'].apply(lambda x: int(float(x.split(':')[0])) if x and ':' in x
                                                                          else int(x.split('.')[0]) if x and '.' in x
                                                                          else int(x) if x else 0)
        print('Past Minutes')
        df_traditional_team = bs_traditional[1][['GAME_ID', 'TEAM_ID', 'FGM', 'FGA', 'FG3M', 'FG3A',
                'FTM', 'FTA', 'OREB', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS', 'PLUS_MINUS']]
        
        bs_advanced = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id).get_data_frames()
        df_advanced_player = bs_advanced[0][['GAME_ID', 'TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME', 'OFF_RATING', 'DEF_RATING', 
                 'OREB_PCT', 'REB_PCT', 'EFG_PCT',  'USG_PCT', 'PIE']]
        df_advanced_team = bs_advanced[1][['GAME_ID', 'TEAM_ID', 'OFF_RATING', 'DEF_RATING',  'OREB_PCT',
                        'REB_PCT', 'EFG_PCT', 'PACE']]
        df_player = pd.merge(df_traditional_player, df_advanced_player, on=['GAME_ID', 'TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME'])
        keep_float_cols = ['OFF_RATING', 'DEF_RATING', 'OREB_PCT', 'REB_PCT', 'EFG_PCT', 'USG_PCT', 'PIE', 'PACE']
        df_player['ENTERED_GAME'] = df_player['FGM'].apply(lambda x: 0 if pd.isna(x) else 1)
        cols_to_convert = [col for col in df_player.select_dtypes(include='float64').columns if col not in keep_float_cols]
        df_player[cols_to_convert] = df_player[cols_to_convert].astype('Int64')
        df_player.fillna(0, inplace=True)
        
        df_team = pd.merge(df_traditional_team, df_advanced_team, on=['GAME_ID', 'TEAM_ID'])
        cols_to_convert = [col for col in df_team.select_dtypes(include='float64').columns if col not in keep_float_cols]
        df_team[cols_to_convert] = df_team[cols_to_convert].astype('Int64')
        return df_player, df_team
    except Exception as e:
        print(f"Error retrieving data for game id {game_id}: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
def build_game_stats_tables(games_table):
    game_ids = games_table['Game_ID'].tolist()
    dfs_player = []
    dfs_team = []
    count = 0
    for game_id in game_ids:
        count += 1
        if count % 10 == 0:
            print(f"Fetching game stats for game {count}")
        if count % 100 == 0:
            print(f"Sleeping for 60 seconds...")
            time.sleep(60)
        df_player, df_team = fetch_game_stats_tables(game_id)
        dfs_player.append(df_player)
        dfs_team.append(df_team)
        time.sleep(2)
    player_game_stats = pd.concat(dfs_player, ignore_index=True)
    team_game_stats = pd.concat(dfs_team, ignore_index=True)
    return player_game_stats, team_game_stats

def build_games_table(teamids = TEAMIDS):
    dfs = []
    for teamid in teamids:
        for i in range(0, 5):
            season = f'20{20 + i}-{21+i}'
            print(teamid, season)
            for season_type in ['Regular Season', 'Playoffs']:
                try:
                    df = teamgamelog.TeamGameLog(team_id = teamid, season = season, season_type_all_star=season_type).get_data_frames()[0]
                    df['SEASON_ID'] = 22020 + i
                    df['SEASON_TYPE'] = season_type
                    dfs.append(df[['Game_ID', 'GAME_DATE', 'MATCHUP', 'PTS', 'SEASON_ID', 'SEASON_TYPE']])
                except Exception as e:
                    print(f"Error retrieving data for team {teamid} season {season}: {e}")
                time.sleep(2)
    df = pd.concat(dfs)
    return format_games_table(df)

def get_player_info(player_id):
    try:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df = player_info.get_data_frames()[0]
        # print(df.columns)
        print(df['DISPLAY_FIRST_LAST'])
        details = df[['PERSON_ID', 'FIRST_NAME', 'LAST_NAME', 'DISPLAY_FIRST_LAST',
                      'HEIGHT', 'WEIGHT', 'POSITION', 'SCHOOL', 'COUNTRY', 'BIRTHDATE',
                      'FROM_YEAR', 'DRAFT_YEAR', 'DRAFT_ROUND', 'DRAFT_NUMBER']]
        return details
    except Exception as e:
        print(f"Error retrieving info for player {player_id}: {e}")
        return None
    
def build_players_table(player_ids):
    dfs = []
    for player_id in player_ids:
        df = get_player_info(player_id)
        dfs.append(df)
        time.sleep(2)
    player_info = pd.concat(dfs, ignore_index=True)
    player_info = player_info[player_info['HEIGHT'] != '']
    player_info['HEIGHT'] = player_info['HEIGHT'].apply(lambda x: int(x.split('-')[0])*12 + int(x.split('-')[1])*1 if isinstance(x, str) else x)
    player_info['BIRTHDATE'] = pd.to_datetime(player_info['BIRTHDATE']).dt.strftime('%Y-%m-%d')
    return player_info.rename(columns = {'PERSON_ID': 'PLAYER_ID', 'DISPLAY_FIRST_LAST':'PLAYER_NAME'})

def update_data(date):
    warnings.filterwarnings("ignore")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        df = scoreboardv2.ScoreboardV2(game_date=date)
    except:
        pass
    new_games = update_games_table(date).dropna()
    new_games['GAME_DATE'] = new_games['GAME_DATE'].apply(lambda d: d.isoformat() if pd.notnull(d) else None)
    float_cols = new_games.select_dtypes(include='float64').columns
    new_games[float_cols] = new_games[float_cols].astype(int)
    dfp, dft = build_game_stats_tables(new_games)
    playas = supabase.table('players').select('*').execute().data
    playerids = [x['player_id'] for x in playas]
    new_players = set(dfp.PLAYER_ID) - set(playerids)
    if len(new_players) > 0:
        new_players_df = build_players_table(new_players)
        new_players_df['WEIGHT'] = new_players_df['WEIGHT'].fillna(200).astype(int)
        dfp = dfp[dfp.PLAYER_ID.isin(list(set(new_players_df.PLAYER_ID) | set(playerids)))]
        new_players_df.rename(columns=str.lower, inplace=True)
        response2 = supabase.table("players").upsert(new_players_df.to_dict(orient='records')).execute()
    else:
        response2 = None
    new_games.rename(columns=str.lower, inplace=True)
    dfp.rename(columns=str.lower, inplace=True)
    dft.rename(columns=str.lower, inplace=True)
    response1 = supabase.table("games").upsert(new_games.to_dict(orient='records')).execute()
    response3 = supabase.table("game_stats_player").upsert(dfp.to_dict(orient='records')).execute()
    response4 = supabase.table("game_stats_team").upsert(dft.dropna().to_dict(orient='records')).execute()
    return response1, response2, response3, response4


