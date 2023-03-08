#!/usr/bin/env bash

set -e -o pipefail

cd "$(dirname "$0")"

rev="$(git rev-parse HEAD)"

# determine the tag to use for the devops-console-backend image
if [[ -z "$REV" ]]; then
	echo "Enter the tag you want to use for the docker image (default: $rev):"
	read -r REV
	if [[ -z "$REV" ]]; then
		REV="$rev"
	fi
fi
FULL_TAG="croixbleueqc/devops-console-backend:$REV"

# devops-console-backend image
docker build -t "$FULL_TAG" .

# publish to dockerhub
echo "Publish to Dockerhub? [Y/n]"
read -r answer
if [[ -z "$answer" || "$answer" == "y" || "$answer" == "Y" ]]; then
	docker login

	docker push "$FULL_TAG"
fi
