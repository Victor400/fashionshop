# catalog/migrations/0003_create_core_tables.py
from django.db import migrations

CREATE_SQL = r"""
-- brand
CREATE TABLE IF NOT EXISTS public.brand (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE
);

-- category
CREATE TABLE IF NOT EXISTS public.category (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  display_name TEXT,
  slug TEXT NOT NULL UNIQUE
);

-- product
CREATE TABLE IF NOT EXISTS public.product (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  sku  TEXT NOT NULL UNIQUE,
  description TEXT,
  price NUMERIC(10,2) NOT NULL,
  stock INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL,
  category_id BIGINT NOT NULL REFERENCES public.category(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  brand_id    BIGINT NOT NULL REFERENCES public.brand(id)    ON UPDATE CASCADE ON DELETE RESTRICT
);
"""

DROP_SQL = r"""
DROP TABLE IF EXISTS public.product;
DROP TABLE IF EXISTS public.category;
DROP TABLE IF EXISTS public.brand;
"""

class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_alter_brand_options_alter_category_options_and_more"),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL),
    ]
