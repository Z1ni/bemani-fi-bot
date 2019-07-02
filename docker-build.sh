#!/bin/sh
docker build --build-arg GIT_COMMIT=$(git describe --always) $@