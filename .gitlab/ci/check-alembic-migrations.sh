#!/bin/bash
#
# Detect a diverged Alembic migration history between this branch and main.
#
# The data-source-management API applies its Alembic migrations as a single
# linear chain (each revision points at its parent via down_revision). If a
# branch adds a new migration while main independently adds another, both new
# revisions hang off the same parent. Merging the branch then produces two
# Alembic heads and `alembic upgrade head` fails, taking the dsm-api down.
#
# This script fails when BOTH of the following are true:
#   * the branch contains a revision that does not exist on main, AND
#   * main contains a revision that does not exist on the branch.
#
# In that case the branch must merge/rebase onto main and re-point its
# migration's down_revision at main's current head before it can be merged.

set -euo pipefail

# Run from the repository root so the paths below are independent of the
# caller's current working directory.
cd "$(git rev-parse --show-toplevel)"

ALEMBIC_DIR="data-source-management/api/app/alembic/versions"
MAIN_BRANCH="${CI_DEFAULT_BRANCH:-main}"

echo "Fetching origin/${MAIN_BRANCH} ..."
git fetch --quiet --depth=1 origin "${MAIN_BRANCH}"
MAIN_REF="FETCH_HEAD"

# Print the Alembic revision id of every migration file present at a git ref.
list_revisions() {
  local ref="$1"
  git ls-tree -r --name-only "${ref}" -- "${ALEMBIC_DIR}" \
    | grep -E '\.py$' \
    | grep -v '/__init__\.py$' \
    | while read -r file; do
        git show "${ref}:${file}" \
          | grep -E '^revision(:[^=]*)? *=' \
          | head -n1 \
          | sed -E 's/^revision(:[^=]*)? *= *["'\'']([^"'\'']+)["'\''].*/\2/'
      done \
    | sort -u
}

branch_revs="$(list_revisions HEAD)"
main_revs="$(list_revisions "${MAIN_REF}")"

branch_only="$(comm -23 <(echo "${branch_revs}") <(echo "${main_revs}"))"
main_only="$(comm -13 <(echo "${branch_revs}") <(echo "${main_revs}"))"

echo ""
echo "Revisions only on this branch:"
echo "${branch_only:-  (none)}" | sed 's/^/  /'
echo "Revisions only on ${MAIN_BRANCH}:"
echo "${main_only:-  (none)}" | sed 's/^/  /'
echo ""

if [ -n "${branch_only}" ] && [ -n "${main_only}" ]; then
  echo "ERROR: Alembic migration history has diverged from ${MAIN_BRANCH}." >&2
  echo "" >&2
  echo "This branch adds migration(s) while ${MAIN_BRANCH} has migration(s) that" >&2
  echo "this branch does not contain. Merging would create multiple Alembic heads" >&2
  echo "and break 'alembic upgrade head' in the data-source-management API." >&2
  echo "" >&2
  echo "Fix: merge or rebase this branch onto ${MAIN_BRANCH}, then set your new" >&2
  echo "migration's down_revision to ${MAIN_BRANCH}'s current head." >&2
  exit 1
fi

echo "OK: Alembic migration history is consistent with ${MAIN_BRANCH}."
