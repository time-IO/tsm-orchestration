#!/usr/bin/env bash
# Smoke test of the FROST context API; run where port 8081 of the instance is reachable.
# Needs FROST_CONTEXT_API_URL and FROST_CONTEXT_API_TOKEN; creates and deletes schema `smoketest`.
set -u
url="${FROST_CONTEXT_API_URL:?}/contexts"
auth="Authorization: Bearer ${FROST_CONTEXT_API_TOKEN:?}"
ctx='<Context path="/smoketest" docBase="/share/FROST-Server.war"><Parameter name="a" value="b"/></Context>'
rc=0

# expect <status> <description> <curl args...>
expect() {
    local want="$1" what="$2"
    shift 2
    local got
    got=$(curl -s -o /dev/null -w '%{http_code}' "$@")
    if [ "$got" = "$want" ]; then echo "ok   $what"; else echo "FAIL $what: want $want, got $got"; rc=1; fi
}

expect 401 "no token" -X PUT "$url/smoketest" -d "$ctx"
expect 401 "wrong token" -X PUT "$url/smoketest" -H "Authorization: Bearer wrong" -d "$ctx"
expect 400 "invalid schema" -X PUT "$url/a.b" -H "$auth" -d "$ctx"
expect 400 "not a Context" -X PUT "$url/smoketest" -H "$auth" -d "<Server/>"
expect 400 "DOCTYPE rejected" -X PUT "$url/smoketest" -H "$auth" \
    -d '<!DOCTYPE c [<!ENTITY x SYSTEM "file:///etc/passwd">]><Context path="/smoketest" docBase="/share/FROST-Server.war"/>'
expect 200 "put" -X PUT "$url/smoketest" -H "$auth" -d "$ctx"
expect 200 "put unchanged" -X PUT "$url/smoketest" -H "$auth" -d "$ctx"
expect 200 "list" "$url" -H "$auth"
expect 200 "delete" -X DELETE "$url/smoketest" -H "$auth"
exit $rc
