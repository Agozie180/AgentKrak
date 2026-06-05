@echo off
setlocal
docker run --rm -v "%CD%:/workspace" -w /workspace agentkrak kraken %*
