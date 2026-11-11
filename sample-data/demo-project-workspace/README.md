# Demo project (MCP target)

A deliberately tiny service the J.A.R.V.I.S. host MCP server is authorized to
access during the live demo. `test_app.py` fails on purpose until the bug in
`greeting()` is fixed through the approved-edit workflow.

    python -m pytest -q          # 1 failing test before the fix
    docker compose up -d --build # http://127.0.0.1:8081/greet/Ada
