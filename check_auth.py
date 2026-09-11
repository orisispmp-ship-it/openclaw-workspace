import sqlite3
conn = sqlite3.connect(r'C:\Users\orisi\.openclaw\agents\main\agent\openclaw-agent.sqlite')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
for t in c.fetchall():
    print('=== Table:', t[0], '===')
    c2 = conn.cursor()
    c2.execute(f'SELECT * FROM "{t[0]}"')
    rows = c2.fetchall()
    for r in rows:
        print(r)
    print()
conn.close()
