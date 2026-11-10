#!/usr/bin/env bash
# Periodically pings every FROST webapp so its DB pool stays warm, then runs CMD.

CONTEXT_DIR="${CATALINA_HOME:-/usr/local/tomcat}/conf/Catalina/localhost"
BASE_URL="http://localhost:8080"
export BASE_URL

log() { echo "frost-keepalive: $*"; }

ping_one() {
    local out rc status
    out=$(timeout 5 wget -S -O /dev/null -t 1 \
        "$BASE_URL/$1/v1.1/Things?\$top=1&\$select=id" 2>&1)
    rc=$?
    case $rc in
        0) echo ok ;;
        124) echo "$1: timeout" ;;
        8)
            status=$(grep -o 'HTTP/[0-9.]* [0-9]*' <<<"$out" | tail -n 1)
            echo "$1: HTTP ${status##* }"
            ;;
        4) grep -q refused <<<"$out" && echo "$1: connect" || echo "$1: network error" ;;
        *) echo "$1: wget exit $rc" ;;
    esac
}
export -f ping_one

run_round() {
    local start=$SECONDS ok=0 failures=() results r joined
    mapfile -t results < <(
        find "$CONTEXT_DIR" -maxdepth 1 -name '*.xml' -printf '%f\n' 2>/dev/null \
            | sed 's/\.xml$//' \
            | xargs -r -P 4 -I{} bash -c 'ping_one "$1"' _ {}
    )
    for r in "${results[@]}"; do
        if [[ $r == ok ]]; then ok=$((ok + 1)); else failures+=("$r"); fi
    done
    if ((${#failures[@]})); then
        printf -v joined '%s, ' "${failures[@]}"
        joined=" [${joined%, }]"
    fi
    log "$ok ok, ${#failures[@]} failed${joined}, $((SECONDS - start))s"
}

keepalive_loop() {
    until timeout 5 wget -q -O /dev/null -t 1 "$BASE_URL/"; do sleep 5; done
    while true; do
        run_round
        sleep "$1"
    done
}

interval="${FROST_KEEPALIVE_INTERVAL:-0}"
if ! [[ $interval =~ ^[0-9]+$ ]]; then
    log "invalid FROST_KEEPALIVE_INTERVAL '$interval', disabled"
    interval=0
fi
if ((10#$interval > 0)); then
    log "every $((10#$interval))s"
    keepalive_loop "$((10#$interval))" &
else
    log "disabled"
fi

exec "$@"
