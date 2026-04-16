import type { ColDef } from 'ag-grid-community'

/**
 * AG Grid 공통 기본 컬럼 설정
 * - 모든 컬럼 리사이즈 가능
 * - flex 비율 기반 너비 배분
 * - 셀 텍스트 잘림 시 브라우저 툴팁 표시
 */
export const defaultColDef: ColDef = {
  sortable: true,
  resizable: true,
  flex: 1,
  minWidth: 60,
  tooltipValueGetter: (params) => params.value,
}

/**
 * 컬럼 정의에 headerTooltip 자동 추가
 * - headerName 값을 headerTooltip으로 복사하여 헤더 잘림 시 툴팁 표시
 */
export function withHeaderTooltips(cols: ColDef[]): ColDef[] {
  return cols.map((col) => ({
    ...col,
    headerTooltip: col.headerTooltip ?? (col as any).headerName,
  }))
}
