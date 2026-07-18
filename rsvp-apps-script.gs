/**
 * Backend RSVP & Ucapan untuk Undangan Pernikahan (Google Apps Script)
 * ======================================================================
 * Skrip ini membuat "API" gratis di atas Google Sheets untuk menyimpan
 * RSVP & ucapan tamu secara permanen, dan menampilkannya kembali ke
 * semua tamu di wall ucapan pada halaman undangan (index.html / u/*.html).
 *
 * CARA PASANG (sekali saja, ±5 menit):
 *   1. Buka https://sheets.google.com -> buat spreadsheet baru
 *      (nama bebas, mis. "RSVP Bayu & Triana").
 *   2. Menu Extensions/Ekstensi -> Apps Script.
 *   3. Hapus isi default "Code.gs", lalu tempel SELURUH isi file ini.
 *   4. Simpan proyek (Ctrl+S / ikon simpan), beri nama proyek bebas.
 *   5. Klik Deploy -> New deployment (Deployment baru).
 *        - Klik ikon gerigi di sebelah "Select type" -> pilih "Web app".
 *        - Execute as: Me (akun Anda).
 *        - Who has access: Anyone (Siapa saja).
 *      Klik Deploy, lalu Authorize access dan izinkan -- ini skrip milik
 *      Anda sendiri, Google hanya minta konfirmasi karena skrip
 *      membaca/menulis Spreadsheet Anda.
 *   6. Salin "Web app URL" yang muncul (diakhiri dengan /exec).
 *   7. Tempel URL itu sebagai nilai `rsvpEndpoint` di dalam objek WEDDING
 *      pada index.html (sumber tunggal desain undangan), lalu generate
 *      ulang undangan per tamu (python3 generate_undangan.py) supaya
 *      semua file u/*.html ikut memakainya.
 *
 * CATATAN:
 *   - Endpoint ini bersifat publik (siapa pun yang tahu URL-nya bisa
 *     mengirim data) -- sama seperti filosofi keamanan undangan ini
 *     secara keseluruhan (obscurity lewat token acak per tamu, bukan
 *     autentikasi sungguhan). Cukup untuk kebutuhan RSVP tamu biasa.
 *   - Setiap kali Anda mengubah isi skrip ini, buat deployment baru lagi
 *     (Deploy -> Manage deployments -> Edit -> versi baru) supaya
 *     perubahan benar-benar ikut ter-deploy ke Web app URL yang sama.
 *   - Semua data tersimpan di tab sheet "RSVP" pada spreadsheet yang sama
 *     dengan skrip ini (dibuat otomatis saat data pertama masuk).
 */

var SHEET_NAME = "RSVP";

function doGet(e) {
  var sheet = getSheet_();
  var rows = sheet.getDataRange().getValues();
  var data = [];
  for (var i = 1; i < rows.length; i++) {
    if (!rows[i][1]) continue; // lewati baris kosong
    data.push({
      name: String(rows[i][1]),
      attendance: String(rows[i][2]),
      message: String(rows[i][3])
    });
  }
  data.reverse(); // ucapan terbaru tampil paling atas
  return jsonOutput_({ ok: true, data: data });
}

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var name = String(body.name || "").trim().slice(0, 100);
    var attendance = body.attendance === "Hadir" ? "Hadir" : "Tidak Hadir";
    var message = String(body.message || "").trim().slice(0, 1000);

    if (!name || !message) {
      return jsonOutput_({ ok: false, error: "Nama dan ucapan wajib diisi." });
    }

    getSheet_().appendRow([new Date(), name, attendance, message]);
    return jsonOutput_({ ok: true });
  } catch (err) {
    return jsonOutput_({ ok: false, error: String(err) });
  }
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(["Waktu", "Nama", "Kehadiran", "Ucapan"]);
  }
  return sheet;
}

function jsonOutput_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
