#!/usr/bin/env bash
#
# Continuously collect labeled training data by playing ONE game per process,
# looping forever. This design is deliberate:
#
#   * One game per process — a dropped Showdown connection ends only the current
#     game. With buffered logging (game_logger.flush_battle) that game's turns are
#     simply discarded (no partial/unlabeled data), and the loop starts a fresh
#     process for the next game. Daisy-chaining (`player.py N`) drops the whole run.
#
#   * Per-game timeout — when the websocket connection drops, poke-env hangs on the
#     dead socket instead of exiting. The timeout kills a stuck game so the loop
#     keeps going unattended.
#
# Usage:
#   ./collect.sh [depth] [game_timeout_seconds]
#       depth                 minimax search depth   (default 6)
#       game_timeout_seconds  kill a game after this  (default 1200 = 20 min)
#
# Stop:
#   touch STOP_COLLECTING   # graceful: stops after the current game finishes
#   pkill -f collect.sh     # immediate: also loses the in-progress game only

cd "$(dirname "$0")" || exit 1

DEPTH="${1:-6}"
GAME_TIMEOUT="${2:-1200}"
STOP_FILE="STOP_COLLECTING"
LOG="collect.log"

# Run a command with a portable timeout (macOS has no `timeout` by default).
run_with_timeout() {
    local secs="$1"; shift
    "$@" &
    local pid=$!
    ( sleep "$secs"; kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null ) &
    local watcher=$!
    wait "$pid" 2>/dev/null
    local code=$?
    kill -9 "$watcher" 2>/dev/null
    return "$code"
}

rm -f "$STOP_FILE"
games=0
wins_file=$(mktemp)

echo "[$(date '+%F %T')] collector started (depth $DEPTH, per-game timeout ${GAME_TIMEOUT}s)." | tee -a "$LOG"
echo "[$(date '+%F %T')] stop gracefully with: touch $(pwd)/$STOP_FILE" | tee -a "$LOG"

while [ ! -f "$STOP_FILE" ]; do
    games=$((games + 1))
    echo "[$(date '+%F %T')] === game $games starting ===" >> "$LOG"
    run_with_timeout "$GAME_TIMEOUT" python3 player.py 1 --depth "$DEPTH" >> "$LOG" 2>&1
    code=$?
    echo "[$(date '+%F %T')] === game $games exited (code $code) ===" >> "$LOG"
    sleep 5
done

rm -f "$STOP_FILE" "$wins_file"
echo "[$(date '+%F %T')] collector stopped after $games game attempt(s)." | tee -a "$LOG"
