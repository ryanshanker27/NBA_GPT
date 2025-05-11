#!/usr/bin/env python3
import os
# from config import Config
import datetime
import argparse
from helpers import update_data  

def main():
    parser = argparse.ArgumentParser(
        description="Fetch and upsert today's NBA data into Supabase"
    )
    two_days_ago = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    parser.add_argument(
        "--date",
        type=str,
        default=two_days_ago,
        help="Date for update in YYYY‑MM‑DD format (default: two days ago)"
    )
    args = parser.parse_args()

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in env")

    # Update
    print(f"[{datetime.datetime.now().isoformat()}] Starting update for {args.date}")
    response = update_data(args.date)
    print(f"[{datetime.datetime.now().isoformat()}] Update complete: {response}")

if __name__ == "__main__":
    main()
