# Python Tower Defense

A fun tower defense game built with `pygame`.

## Run

1. Install dependencies in the cloned project folder:

```bash
python3 -m pip install -r requirements.txt
```

2. Run the game:

```bash
python3 main.py
```

On Windows, use `py main.py` if `python3` is not available.

## Shared Wiki

The Wiki can be edited by any player and shared through Supabase. All players must use the same Supabase project.

1. Create a Supabase project and run the SQL in `shared_wiki.sql` from its SQL Editor.
2. Copy the project URL and anon/public key from the project API settings.
3. Set these environment variables before launching the game:

```bash
export TOWER_WIKI_SUPABASE_URL="https://your-project.supabase.co"
export TOWER_WIKI_SUPABASE_ANON_KEY="your-anon-public-key"
python3 main.py
```

In the Wiki window, choose **New Page** to create a titled page, or choose **Edit** to change the current page. Press `Ctrl+S` or click **Save** to publish edits. Other connected players receive updates while viewing the Wiki. Without the Supabase settings, edits are stored only in the local `wiki_local.json` file. Public write access means anyone with the game and project settings can change Wiki pages.

## Controls

- Left-click to place a tower.
- Press `R` to restart after game over.
- unlock new towers
- can you get the secret towers?
- Can you get sickman-stickman to come to your screen?

## Goal

Stop enemies from reaching the end of the path using towers placed along the route.

## message

Sickman-stickman here, wishing you a fun game!
