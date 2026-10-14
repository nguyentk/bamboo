#!/bin/sh
# Create (or update) the Bamboo triage labels on the GitHub repository.
# Requires the GitHub CLI (`gh`), authenticated with write access to the repository.
#
# Usage: sh misc/scripts/setup_github_labels.sh [owner/repo]

set -e

REPO="${1:-}"
REPO_ARGS=""
if [ -n "$REPO" ]; then
    REPO_ARGS="--repo $REPO"
fi

label() {
    # --force updates the color/description if the label already exists.
    gh label create "$1" --color "$2" --description "$3" --force $REPO_ARGS
}

label "P0-Blocker" "b60205" "Blocks release, crash or data loss - fix immediately"
label "P1-High" "d93f0b" "Serious bug, fix within the sprint"
label "P2-Normal" "fbca04" "Normal bug or feature"
label "P3-Low" "0e8a16" "Low priority"

label "area/core" "1d76db" "Core, servers, scene"
label "area/editor" "5319e7" "Editor and tools"
label "area/render" "0052cc" "Rendering"
label "area/platform" "006b75" "Platforms, mobile, web"
label "area/ci" "c5def5" "Build system, CI, packaging"
label "area/unity-port" "f9d0c4" "Unity to Bamboo porting pipeline"

echo "Bamboo labels are set up."
