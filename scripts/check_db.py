import django
django.setup()
from django.db import connection as c

with c.cursor() as cur:
    cur.execute('SHOW search_path;')
    print('search_path =', cur.fetchone()[0])

print('\n-- tables in fashionshop/public --')
with c.cursor() as cur:
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type='BASE TABLE'
          AND table_schema IN ('fashionshop','public')
        ORDER BY 1,2;
    """)
    rows = cur.fetchall()
    for s,t in rows:
        print(f'  {s}.{t}')
    print('\nexpected catalog tables:')
    for s,t in rows:
        if t in ('brand','category','product','catalog_brand','catalog_category','catalog_product'):
            print(f'  FOUND: {s}.{t}')
