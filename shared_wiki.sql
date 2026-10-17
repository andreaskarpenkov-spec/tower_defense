create table if not exists public.game_wiki_pages (
    page_id text primary key,
    content text not null check (char_length(content) <= 12000),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.game_wiki_pages
    add column if not exists created_at timestamptz not null default now();
alter table public.game_wiki_pages
    drop constraint if exists game_wiki_pages_page_id_check;
alter table public.game_wiki_pages
    add constraint game_wiki_pages_page_id_check
    check (char_length(page_id) between 1 and 40);

alter table public.game_wiki_pages enable row level security;
grant select, insert, update on public.game_wiki_pages to anon, authenticated;

drop policy if exists "Anyone can read game wiki" on public.game_wiki_pages;
create policy "Anyone can read game wiki"
    on public.game_wiki_pages for select
    to anon, authenticated
    using (true);

drop policy if exists "Anyone can create game wiki pages" on public.game_wiki_pages;
create policy "Anyone can create game wiki pages"
    on public.game_wiki_pages for insert
    to anon, authenticated
    with check (true);

drop policy if exists "Anyone can edit game wiki pages" on public.game_wiki_pages;
create policy "Anyone can edit game wiki pages"
    on public.game_wiki_pages for update
    to anon, authenticated
    using (true)
    with check (true);

create or replace function public.set_game_wiki_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists game_wiki_pages_updated_at on public.game_wiki_pages;
create trigger game_wiki_pages_updated_at
    before update on public.game_wiki_pages
    for each row execute function public.set_game_wiki_updated_at();