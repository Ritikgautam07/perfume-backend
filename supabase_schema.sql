-- Run this in the Supabase SQL editor (Project -> SQL Editor -> New query)

create extension if not exists "pgcrypto";

-- ============ CATEGORIES ============
create table categories (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  icon text,
  price_min numeric not null,
  price_max numeric not null,
  description text,
  created_at timestamptz default now()
);

-- ============ PRODUCTS ============
create table products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  description text,
  price numeric not null check (price > 0),
  category_id uuid references categories(id) on delete set null,
  mood_tags text[] default '{}',
  luxury_score int default 50 check (luxury_score between 0 and 100),
  freshness_score int default 50 check (freshness_score between 0 and 100),
  longevity_hours int default 6,
  image_url text,
  stock int default 100,
  is_trending boolean default false,
  is_ai_recommended boolean default false,
  created_at timestamptz default now()
);

-- ============ PACK TIERS (e.g. "any 3 minis for ₹500") ============
create table pack_tiers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  num_items int not null,
  flat_price numeric not null,
  description text
);

-- ============ PROFILES (extends Supabase auth.users) ============
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text,
  phone text,
  loyalty_points int default 0,
  has_used_first_order_discount boolean default false,
  created_at timestamptz default now()
);

-- Auto-create a profile row whenever someone signs up via Supabase Auth
create function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, name) values (new.id, new.raw_user_meta_data->>'name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============ DISCOUNT CODES ============
create table discount_codes (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  percent_off numeric default 0,
  flat_off numeric default 0,
  first_order_only boolean default false,
  max_uses int,
  used_count int default 0,
  active boolean default true,
  expires_at timestamptz
);

-- ============ ORDERS ============
create table orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete set null,
  items jsonb not null,
  subtotal numeric not null,
  discount_code text,
  discount_amount numeric default 0,
  total numeric not null,
  status text default 'created', -- created | paid | failed | shipped | delivered
  razorpay_order_id text,
  razorpay_payment_id text,
  loyalty_points_earned int default 0,
  created_at timestamptz default now()
);

-- ============ LOYALTY TRANSACTIONS ============
create table loyalty_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  points int not null,
  type text not null, -- 'earn' or 'redeem'
  order_id uuid references orders(id) on delete set null,
  created_at timestamptz default now()
);

-- ============ ROW LEVEL SECURITY ============
-- The backend talks to Supabase using the service-role key, which bypasses RLS entirely.
-- Enable RLS anyway so nothing is exposed if you ever query these tables directly
-- from the frontend using the anon/public key.
alter table products enable row level security;
alter table categories enable row level security;
alter table pack_tiers enable row level security;
alter table profiles enable row level security;
alter table orders enable row level security;
alter table loyalty_transactions enable row level security;
alter table discount_codes enable row level security;

create policy "Public can read products" on products for select using (true);
create policy "Public can read categories" on categories for select using (true);
create policy "Public can read pack tiers" on pack_tiers for select using (true);
create policy "Users can read own profile" on profiles for select using (auth.uid() = id);
create policy "Users can read own orders" on orders for select using (auth.uid() = user_id);
create policy "Users can read own loyalty history" on loyalty_transactions for select using (auth.uid() = user_id);

-- ============ SEED DATA ============
insert into categories (name, slug, icon, price_min, price_max, description) values
  ('Daily Collection', 'daily', '⚡', 200, 400, 'Everyday wear, light and fresh'),
  ('Premium', 'premium', '💎', 500, 1000, 'Luxury fragrances for special moments'),
  ('Combo Packs', 'combo', '🎁', 500, 500, 'Curated bundles at one flat price'),
  ('Trending', 'trending', '🔥', 200, 1000, 'What everyone is wearing right now'),
  ('AI Recommended', 'ai-recommended', '🧪', 200, 1000, 'Picked by our AI Scent Finder');

insert into pack_tiers (name, num_items, flat_price, description) values
  ('Mini Combo', 3, 500, 'Pick any 3 minis for a flat ₹500');

insert into discount_codes (code, percent_off, first_order_only, active) values
  ('WELCOME15', 15, true, true);

-- Sample products — swap image_url for your own product renders
insert into products (name, slug, description, price, category_id, mood_tags, luxury_score, freshness_score, longevity_hours, image_url, is_trending, is_ai_recommended)
select 'Cyber Oud', 'cyber-oud', 'A bold, futuristic oud with smoky depth.', 899,
  (select id from categories where slug = 'premium'),
  array['powerful','luxury'], 92, 70, 8, 'https://example.com/cyber-oud.png', true, true;

insert into products (name, slug, description, price, category_id, mood_tags, luxury_score, freshness_score, longevity_hours, image_url, is_trending)
select 'Ocean Mist', 'ocean-mist', 'Crisp aquatic notes for an all-day fresh feel.', 349,
  (select id from categories where slug = 'daily'),
  array['fresh','daily_wear'], 55, 88, 6, 'https://example.com/ocean-mist.png', true;

insert into products (name, slug, description, price, category_id, mood_tags, luxury_score, freshness_score, longevity_hours, image_url, is_ai_recommended)
select 'Silver Noir', 'silver-noir', 'Elegant and refined, with a silvery metallic edge.', 749,
  (select id from categories where slug = 'premium'),
  array['luxury','fresh'], 85, 65, 7, 'https://example.com/silver-noir.png', true;
