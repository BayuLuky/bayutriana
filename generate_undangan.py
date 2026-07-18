#!/usr/bin/env python3
"""
Generator Undangan Digital Per-Tamu (versi statis, tanpa backend)
===================================================================
Membaca daftar tamu dari CSV, lalu membuat SATU file HTML terpisah
untuk setiap tamu. Nama tamu langsung "dipanggang" ke dalam file
masing-masing (bukan lewat parameter URL), dan nama file memakai
token acak -- supaya:

  1. Setiap tamu punya URL sendiri: https://domainanda.com/u/{token}.html
  2. Isi satu file tidak membocorkan nama/token tamu lain, karena
     setiap file cuma berisi datanya sendiri.

CATATAN PENTING (baca ini):
Ini TETAP personalisasi + obscurity, BUKAN keamanan sungguhan.
Siapa pun yang PUNYA salah satu link tetap bisa membuka & mengisi
RSVP-nya -- tidak ada verifikasi identitas nyata. Untuk keamanan
sungguhan (PIN tervalidasi server, RSVP terkunci di database),
perlu backend -- lihat dokumen arsitektur yang sudah dibuat
sebelumnya.

CARA PAKAI:
  1. Edit guest-data/daftar-tamu-contoh.csv (atau buat CSV baru)
     dengan kolom: nama, grup, max_pax
  2. Jalankan: python3 generate_undangan.py
  3. Hasilnya ada di folder output/u/ -- unggah SEMUA isi folder itu
     ke hosting statis Anda (Netlify, Vercel, GitHub Pages, dst),
     lalu bagikan link dari ringkasan-link.csv ke tamu masing-masing.
"""

import csv
import html
import re
import secrets
from pathlib import Path

# =====================================================================
# KONFIGURASI -- sesuaikan path bila perlu
# =====================================================================
TEMPLATE_PATH = Path("template-base.html")
GUEST_CSV_PATH = Path("guest-data/daftar-tamu-contoh.csv")
OUTPUT_DIR = Path("output/u")
SUMMARY_CSV_PATH = Path("output/ringkasan-link.csv")
BASE_URL = "https://domainanda.com/u"  # GANTI dengan domain hosting Anda


def generate_token(length_bytes: int = 18) -> str:
    """Token acak URL-safe, sumber cryptographically secure (bukan random.choice biasa)."""
    return secrets.token_urlsafe(length_bytes)


def escape_js_string(value: str) -> str:
    """Escape agar aman disisipkan ke dalam string JS berkutip-dua."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_guest_html(template_text: str, guest_name: str) -> str:
    js_safe_name = escape_js_string(guest_name)
    html_safe_name = html.escape(guest_name)

    # 1) Ganti nilai default di objek WEDDING (dipakai JS saat render)
    new_text = template_text.replace(
        'defaultGuest: "Tamu Undangan",',
        f'defaultGuest: "{js_safe_name}",',
        1,
    )
    if new_text == template_text:
        raise RuntimeError(
            "Tidak menemukan baris 'defaultGuest: \"Tamu Undangan\",' di template. "
            "Template mungkin sudah berubah -- sesuaikan skrip ini."
        )
    template_text = new_text

    # 2) Ganti juga teks placeholder di HTML cover (fallback bila JS gagal load)
    new_text = template_text.replace(
        '<p class="cover-guest-name" id="guestName">Tamu Undangan</p>',
        f'<p class="cover-guest-name" id="guestName">{html_safe_name}</p>',
        1,
    )
    if new_text == template_text:
        raise RuntimeError(
            "Tidak menemukan elemen guestName di template -- sesuaikan skrip ini."
        )
    return new_text


def slugify_for_filename_hint(name: str) -> str:
    """Cuma untuk komentar di dalam file, bukan bagian dari URL -- aman berisi nama asli."""
    return re.sub(r"\s+", " ", name).strip()


def main():
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template tidak ditemukan: {TEMPLATE_PATH}")
    if not GUEST_CSV_PATH.exists():
        raise SystemExit(f"CSV daftar tamu tidak ditemukan: {GUEST_CSV_PATH}")

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    used_tokens = set()
    rows_summary = []

    with GUEST_CSV_PATH.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("nama") or "").strip()
            if not name:
                continue
            group = (row.get("grup") or "").strip()
            max_pax = (row.get("max_pax") or "").strip()

            # pastikan token tidak pernah bentrok (praktis mustahil, tapi tetap dicek)
            token = generate_token()
            while token in used_tokens:
                token = generate_token()
            used_tokens.add(token)

            guest_html = build_guest_html(template_text, name)
            # komentar kecil di awal file, memudahkan Anda audit manual filenya milik siapa
            guest_html = (
                f"<!-- Undangan untuk: {slugify_for_filename_hint(name)} "
                f"({group or 'tanpa grup'}) -->\n" + guest_html
            )

            out_path = OUTPUT_DIR / f"{token}.html"
            out_path.write_text(guest_html, encoding="utf-8")

            rows_summary.append(
                {
                    "nama": name,
                    "grup": group,
                    "max_pax": max_pax,
                    "token": token,
                    "url": f"{BASE_URL}/{token}.html",
                }
            )

    with SUMMARY_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["nama", "grup", "max_pax", "token", "url"])
        writer.writeheader()
        writer.writerows(rows_summary)

    print(f"Berhasil membuat {len(rows_summary)} undangan personal di: {OUTPUT_DIR}/")
    print(f"Ringkasan link (untuk Anda kirim satu-satu ke tamu): {SUMMARY_CSV_PATH}")
    print()
    print("PENTING:")
    print("- Jangan unggah ringkasan-link.csv ke hosting publik -- itu berisi")
    print("  pemetaan nama ke link asli, cukup simpan untuk Anda sendiri.")
    print("- Unggah HANYA isi folder output/u/*.html ke hosting statis Anda.")
    print("- Matikan 'directory listing' di hosting Anda supaya folder /u/")
    print("  tidak bisa di-browse dan menampilkan semua nama file token.")


if __name__ == "__main__":
    main()
