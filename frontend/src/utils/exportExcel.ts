/**
 * AG Grid 데이터를 엑셀(CSV) 파일로 다운로드하는 공통 유틸리티
 * @param columnDefs AG Grid 컬럼 정의 배열
 * @param rowData 행 데이터 배열
 * @param filename 파일명 (확장자 제외)
 */
export function exportGridToExcel(
  columnDefs: any[],
  rowData: any[],
  filename: string = '데이터'
) {
  // 헤더 컬럼 추출 (체크박스, No 컬럼 제외)
  const cols = columnDefs.filter(
    (c: any) => c.headerName && c.field && !c.checkboxSelection
  )

  // BOM + CSV 헤더
  const BOM = '\uFEFF'
  const header = cols.map((c: any) => c.headerName).join(',')

  // 행 데이터
  const rows = rowData.map((row: any) =>
    cols.map((c: any) => {
      let val = row[c.field]
      if (val === null || val === undefined) val = ''
      // 쉼표/줄바꿈 포함 시 따옴표 처리
      val = String(val)
      if (val.includes(',') || val.includes('\n') || val.includes('"')) {
        val = '"' + val.replace(/"/g, '""') + '"'
      }
      return val
    }).join(',')
  )

  const csv = BOM + header + '\n' + rows.join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
