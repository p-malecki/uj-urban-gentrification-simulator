#!/usr/bin/env bash
set -e

pushd src > /dev/null

source ./solara-env/bin/activate

solara run app.py &

sleep 2

if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8765
elif command -v open > /dev/null; then
    open http://localhost:8765
elif command -v start > /dev/null; then
    start http://localhost:8765
else
    echo "Open http://localhost:8765 manually"
fi

popd > /dev/null
