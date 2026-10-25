#!/bin/sh
# CT40.A12.Solari.serve.sh -- serve this folder so the page reads the JSON files directly
# (needed only if you edit the JSON and don't want to re-run build_embedded.py).
# Run in WSL/Linux from this folder:  sh CT40.A12.Solari.serve.sh
# then open http://localhost:8040/index.html in your browser.
cd "$(dirname "$0")" && python3 -m http.server 8040
