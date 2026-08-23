#!/usr/bin/env node
// Quan ly cac muc "## Nhat ky trien khai — ... (yyyy-mm-dd...)" theo co che moi (tu 2026-08-08):
// ghi 1 muc MOI dong thoi vao CLAUDE.md (tam, 24h) VA vao dung file History dich (vinh vien), roi
// don cac muc da qua "hom nay" khoi CLAUDE.md (KHONG can ghi lai sang History luc don - da ghi tu
// luc tao). Thay the hoan toan archive-old-entries.mjs cu (dong sau 5 ngay vao 1 file History.md
// chung cho moi module).
//
// Cach dung:
//   node quan-ly-nhat-ky.mjs ghi --dich=<ten-dich> --file=<duong-dan-file-chua-noi-dung-1-khoi>
//     ten-dich hop le: project | extract | engine | report | vision | config
//     (khop cau truc src/drawing_check/ - xem master-architecture/SKILL.md)
//   node quan-ly-nhat-ky.mjs don [--ngay=yyyy-mm-dd] [--kiem-tra]
//
// LUU Y: script nay KHONG tu backup CLAUDE.md/docs/Source/*.md truoc khi ghi - theo dung quy uoc
// CLAUDE.md "truoc MOI lan cap nhat file trong docs/Source/ phai backup", nguoi goi (Claude, trong
// workflow Works_End) phai tu backup TRUOC khi chay lenh nay, khong lam ngam trong nay.

import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const GOC_DU_AN = path.resolve(__dirname, '../../../..')
const CLAUDE_MD = path.join(GOC_DU_AN, 'CLAUDE.md')
const DOCS_SOURCE = path.join(GOC_DU_AN, 'docs', 'Source')

const DICH_HOP_LE = [
  'project', 'extract', 'engine', 'report', 'vision', 'config',
]

const GHI_CHU_BLOCK = `> **Ghi chú:** các mục "Nhật ký triển khai" từ đây tới cuối file có nhãn ngày trong vòng 24h gần
> nhất, tạm giữ ở đây theo đúng quy ước mới (xem mục "Ghi nhớ & Lịch sử triển khai" ở trên) — mỗi
> mục đã có bản sao vĩnh viễn tại \`docs/Source/<khu-vuc>-History.md\` hoặc
> \`docs/Source/Project-History.md\` tương ứng. Phiên \`/Works_End\` kế tiếp sẽ tự xoá các mục đã quá
> 24h khỏi đây (không mất nội dung, vẫn còn trong History). Dòng ghi chú này (không phải heading
> \`## \`, để script \`quan-ly-nhat-ky.mjs\` không nhầm là 1 mục nhật ký) tự xoá khi mục cuối cùng bị
> dọn hết — script tự thêm lại khi có mục mới đầu tiên sau lần dọn sạch.
`

function tenFileDich(dich) {
  return dich === 'project' ? 'Project-History.md' : `${dich}-History.md`
}

// Chi coi la 1 "muc nhat ky that" khi dong dau khop dung dang tieu de + ngay trong ngoac -
// tranh nham voi dong ghi chu (blockquote) o tren, vi dong do cung bat dau tu chu "Nhat ky...".
const MAU_TIEU_DE = /^## Nhật ký triển khai — .*\(\d{4}-\d{2}-\d{2}/

function tach(noiDung) {
  const dong = noiDung.split('\n')
  const chiSoBatDau = dong.findIndex((d) => MAU_TIEU_DE.test(d))
  if (chiSoBatDau === -1) {
    return { phanDauQuyUoc: boGhiChu(noiDung), khoiList: [] }
  }
  const phanDauQuyUoc = boGhiChu(dong.slice(0, chiSoBatDau).join('\n'))
  const khoiList = []
  let viTriHienTai = chiSoBatDau
  for (let i = chiSoBatDau + 1; i <= dong.length; i++) {
    if (i === dong.length || MAU_TIEU_DE.test(dong[i])) {
      // Bo trang trang cuoi moi khoi de khoang cach giua cac khoi luon nhat quan (xem ghepLaiClaudeMd),
      // khong phu thuoc file goc co dong trong o cuoi hay khong.
      khoiList.push(dong.slice(viTriHienTai, i).join('\n').replace(/\s+$/, ''))
      viTriHienTai = i
    }
  }
  return { phanDauQuyUoc, khoiList }
}

function boGhiChu(text) {
  // So khop theo ban .trim() (khong phu thuoc so dong trong o dau/cuoi GHI_CHU_BLOCK) de van nhan
  // ra ghi chu ke ca khi file khong ket thuc bang dung 1 dong trong nhu template literal goc.
  const loi = GHI_CHU_BLOCK.trim()
  return text.includes(loi) ? text.replace(loi, '').replace(/\n{3,}/g, '\n\n') : text
}

function themGhiChuNeuChua(phanDauQuyUoc) {
  if (phanDauQuyUoc.includes(GHI_CHU_BLOCK.trim())) return phanDauQuyUoc
  return phanDauQuyUoc.replace(/\n*$/, '\n\n') + GHI_CHU_BLOCK
}

function trichNgay(dongTieuDe) {
  const m = /\((\d{4})-(\d{2})-(\d{2})/.exec(dongTieuDe)
  if (!m) return null
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
}

function laCungNgay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

function ghepLaiClaudeMd(phanDauQuyUoc, khoiList) {
  if (khoiList.length === 0) return phanDauQuyUoc.replace(/\n*$/, '\n')
  return themGhiChuNeuChua(phanDauQuyUoc) + '\n' + khoiList.join('\n\n') + '\n'
}

function lenhGhi(args) {
  const dich = (args.find((a) => a.startsWith('--dich=')) || '').slice('--dich='.length)
  const duongFile = (args.find((a) => a.startsWith('--file=')) || '').slice('--file='.length)
  if (!DICH_HOP_LE.includes(dich)) {
    throw new Error(`--dich không hợp lệ: "${dich}" — phải là 1 trong: ${DICH_HOP_LE.join(', ')}`)
  }
  if (!duongFile || !existsSync(duongFile)) {
    throw new Error(`--file không tồn tại: "${duongFile}"`)
  }
  const khoiMoi = readFileSync(duongFile, 'utf8').replace(/\s*$/, '')
  if (!MAU_TIEU_DE.test(khoiMoi.split('\n', 1)[0])) {
    throw new Error('Dòng đầu file không đúng dạng "## Nhật ký triển khai — <tiêu đề> (yyyy-mm-dd...)"')
  }

  // 1) Ghi vinh vien vao dung file History dich.
  const tenFile = tenFileDich(dich)
  const duongDich = path.join(DOCS_SOURCE, tenFile)
  if (!existsSync(duongDich)) throw new Error(`Không tìm thấy ${duongDich} — chạy Phase 1 (tạo khung sườn) trước.`)
  const hienCo = readFileSync(duongDich, 'utf8')
  writeFileSync(duongDich, hienCo.replace(/\n*$/, '\n\n') + khoiMoi + '\n', 'utf8')

  // 2) Giu ban sao tam trong CLAUDE.md (den khi bi "don" boi lenh `don` ben duoi).
  const { phanDauQuyUoc, khoiList } = tach(readFileSync(CLAUDE_MD, 'utf8'))
  khoiList.push(khoiMoi)
  writeFileSync(CLAUDE_MD, ghepLaiClaudeMd(phanDauQuyUoc, khoiList), 'utf8')

  console.log(`Đã ghi mục mới vào ${tenFile} (vĩnh viễn) và CLAUDE.md (tạm, 24h).`)
}

function lenhDon(args) {
  const argNgay = args.find((a) => a.startsWith('--ngay='))
  const kiemTra = args.includes('--kiem-tra')
  const homNay = argNgay
    ? (() => { const [y, m, d] = argNgay.slice('--ngay='.length).split('-').map(Number); return new Date(y, m - 1, d) })()
    : new Date()

  const { phanDauQuyUoc, khoiList } = tach(readFileSync(CLAUDE_MD, 'utf8'))
  const giuLai = []
  const donDi = []
  for (const khoi of khoiList) {
    const dongDau = khoi.split('\n', 1)[0]
    const ngay = trichNgay(dongDau)
    if (ngay && !laCungNgay(ngay, homNay)) {
      donDi.push(dongDau)
    } else {
      giuLai.push(khoi)
    }
  }

  if (donDi.length === 0) {
    console.log('Không có mục nào cũ hơn hôm nay trong CLAUDE.md — không cần dọn.')
    return
  }

  console.log(`Sẽ dọn ${donDi.length} mục khỏi CLAUDE.md (đã có bản vĩnh viễn trong docs/Source/*-History.md từ lúc tạo):`)
  for (const t of donDi) console.log(' -', t)

  if (kiemTra) {
    console.log('\n(--kiem-tra: chưa ghi file nào)')
    return
  }

  writeFileSync(CLAUDE_MD, ghepLaiClaudeMd(phanDauQuyUoc, giuLai), 'utf8')
  console.log(`\nĐã cập nhật CLAUDE.md (còn ${giuLai.length} mục tạm giữ).`)
}

function main() {
  const [lenh, ...rest] = process.argv.slice(2)
  if (lenh === 'ghi') return lenhGhi(rest)
  if (lenh === 'don') return lenhDon(rest)
  console.error('Dùng: node quan-ly-nhat-ky.mjs ghi --dich=<...> --file=<...>  |  node quan-ly-nhat-ky.mjs don [--ngay=yyyy-mm-dd] [--kiem-tra]')
  process.exitCode = 1
}

main()
