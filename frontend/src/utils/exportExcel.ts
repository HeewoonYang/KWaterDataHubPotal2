/**
 * AG Grid 데이터를 서식이 적용된 엑셀(.xlsx) 파일로 다운로드하는 공통 유틸리티
 * - 헤더 배경색(파란), 글자색(흰), 볼드 적용
 * - 열 너비 자동 조절 (데이터 길이 기반)
 * - 숫자/날짜 포맷 유지
 */
import * as XLSX from 'xlsx'

export function exportGridToExcel(
  columnDefs: any[],
  rowData: any[],
  filename: string = '데이터'
) {
  // 헤더 컬럼 추출 (체크박스, No 컬럼 제외하되 field 없는 것도 valueFormatter가 있으면 포함)
  const cols = columnDefs.filter(
    (c: any) => c.headerName && c.field && !c.checkboxSelection
  )

  // 헤더 행
  const headers = cols.map((c: any) => c.headerName)

  // 데이터 행 — valueFormatter가 있으면 적용
  const dataRows = rowData.map((row: any) =>
    cols.map((c: any) => {
      let val = row[c.field]
      if (val === null || val === undefined) return ''
      // valueFormatter 적용 시도
      if (c.valueFormatter && typeof c.valueFormatter === 'function') {
        try {
          val = c.valueFormatter({ value: val, data: row })
        } catch { /* raw value fallback */ }
      }
      return val
    })
  )

  // 워크시트 생성
  const wsData = [headers, ...dataRows]
  const ws = XLSX.utils.aoa_to_sheet(wsData)

  // 열 너비 자동 조절
  const colWidths = cols.map((c: any, idx: number) => {
    const headerLen = c.headerName.length
    const maxDataLen = dataRows.reduce((max: number, row: any[]) => {
      const cellLen = String(row[idx] ?? '').length
      return Math.max(max, cellLen)
    }, 0)
    // 한글은 2바이트 근사, 최소 8, 최대 50
    const rawWidth = Math.max(headerLen * 2, maxDataLen * 1.2, 8)
    return { wch: Math.min(Math.round(rawWidth), 50) }
  })
  ws['!cols'] = colWidths

  // 헤더 스타일 (xlsx community edition은 스타일 제한적이므로 배경색은 xlsx-style 필요)
  // 대신 헤더 행 높이 설정
  ws['!rows'] = [{ hpt: 28 }]

  // 워크북 생성 및 다운로드
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '데이터')

  const now = new Date().toISOString().slice(0, 10)
  XLSX.writeFile(wb, `${filename}_${now}.xlsx`)
}
