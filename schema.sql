-- BÁO CÁO BỘ PHẬN XẾP GIẤY: tạo cơ sở dữ liệu trên Supabase
-- Cách dùng: Supabase > SQL Editor > New query > dán toàn bộ file này > Run.
-- TRƯỚC KHI CHẠY: đổi 'DOI_MAT_KHAU_O_DAY' (cuối file) thành mật khẩu của bạn.
-- Chạy lại file này nhiều lần vẫn an toàn (không mất dữ liệu báo cáo).

create extension if not exists pgcrypto with schema extensions;

-- ========== Bảng dữ liệu ==========
-- Mỗi lần đẩy file Excel lên, toàn bộ số liệu (tg, pd, btp, meta) được lưu thành 1 bản ghi.
--   id = 1: bản đang hiển thị trên báo cáo
--   id = 0: bản ngay trước đó (dự phòng, dùng để khôi phục)
create table if not exists report (
  id         int primary key check (id in (0, 1)),
  data       jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists settings (key text primary key, value text not null);

-- ========== Phân quyền: ai có link chỉ ĐỌC báo cáo; ghi cần mật khẩu ==========
alter table report   enable row level security;
alter table settings enable row level security;

drop policy if exists read_current_report on report;
create policy read_current_report on report for select to anon, authenticated using (id = 1);

revoke all on report, settings from anon, authenticated;
grant select on report to anon, authenticated;

-- ========== Hàm kiểm tra mật khẩu (không mở ra bên ngoài) ==========
create or replace function is_admin(p_pw text)
returns boolean language plpgsql security definer set search_path = public, extensions as $$
declare ok boolean;
begin
  select exists(select 1 from settings where key = 'admin' and value = crypt(coalesce(p_pw, ''), value)) into ok;
  if not ok then perform pg_sleep(1); end if;   -- làm chậm việc dò mật khẩu
  return ok;
end $$;
revoke execute on function is_admin(text) from public, anon, authenticated;

-- ========== Hàm cho chủ báo cáo ==========
create or replace function admin_check(p_pw text)
returns boolean language sql security definer set search_path = public, extensions as $$ select is_admin(p_pw) $$;

-- Đẩy số liệu mới lên (thay toàn bộ bản đang hiển thị, bản cũ giữ lại làm dự phòng)
create or replace function admin_publish_report(p_pw text, p_data jsonb)
returns timestamptz language plpgsql security definer set search_path = public, extensions as $$
declare ts timestamptz := now();
begin
  if not is_admin(p_pw) then raise exception 'Sai mật khẩu.'; end if;
  if p_data is null or jsonb_typeof(p_data -> 'tg') <> 'array' or jsonb_typeof(p_data -> 'pd') <> 'array'
     or jsonb_typeof(p_data -> 'btp') <> 'array' or jsonb_typeof(p_data -> 'meta') <> 'object' then
    raise exception 'Dữ liệu không đúng định dạng (cần tg, pd, btp, meta).';
  end if;
  if jsonb_array_length(p_data -> 'tg') = 0 then raise exception 'Sheet Nhap_TG không có dòng dữ liệu nào.'; end if;
  insert into report (id, data, updated_at)
    select 0, data, updated_at from report where id = 1
  on conflict (id) do update set data = excluded.data, updated_at = excluded.updated_at;
  insert into report (id, data, updated_at) values (1, p_data, ts)
  on conflict (id) do update set data = excluded.data, updated_at = excluded.updated_at;
  return ts;
end $$;

-- Quay lại bản dữ liệu trước đó (đổi chỗ bản hiện tại và bản dự phòng)
create or replace function admin_restore_previous(p_pw text)
returns timestamptz language plpgsql security definer set search_path = public, extensions as $$
declare cur report; prev report;
begin
  if not is_admin(p_pw) then raise exception 'Sai mật khẩu.'; end if;
  select * into cur from report where id = 1;
  select * into prev from report where id = 0;
  if prev.id is null then raise exception 'Chưa có bản dự phòng để khôi phục.'; end if;
  update report set data = prev.data, updated_at = prev.updated_at where id = 1;
  if cur.id is not null then update report set data = cur.data, updated_at = cur.updated_at where id = 0; end if;
  return prev.updated_at;
end $$;

revoke execute on function admin_check(text), admin_publish_report(text, jsonb), admin_restore_previous(text) from public;
grant execute on function admin_check(text), admin_publish_report(text, jsonb), admin_restore_previous(text)
  to anon, authenticated;

-- ========== Mật khẩu ==========
-- ĐỔI MẬT KHẨU Ở DÒNG DƯỚI trước khi chạy (giữ nguyên dấu nháy đơn).
-- Nếu đã có mật khẩu từ lần chạy trước, dòng này giữ nguyên mật khẩu cũ.
insert into settings (key, value) values ('admin', crypt('070715', gen_salt('bf')))
on conflict (key) do nothing;
