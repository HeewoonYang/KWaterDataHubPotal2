/**
 * Ant Design 스타일 토스트 메시지 유틸
 * - alert() 대체용
 * - success / error / warning / info 4종 지원
 */

type MessageType = 'success' | 'error' | 'warning' | 'info'

const ICONS: Record<MessageType, string> = {
  success: `<svg viewBox="64 64 896 896" width="1em" height="1em" fill="#52c41a"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm193.5 301.7l-210.6 292a31.8 31.8 0 01-51.7 0L318.5 484.9c-3.8-5.3 0-12.7 6.5-12.7h46.9c10.2 0 19.9 4.9 25.9 13.3l71.2 98.8 157.2-218c6-8.3 15.6-13.3 25.9-13.3H699c6.5 0 10.3 7.4 6.5 12.7z"/></svg>`,
  error: `<svg viewBox="64 64 896 896" width="1em" height="1em" fill="#ff4d4f"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm165.4 618.2l-66-.3L512 563.4l-99.3 118.4-66.1.3c-4.4 0-8-3.5-8-8 0-1.9.7-3.7 1.9-5.2l130.1-155L340.5 359a8.32 8.32 0 01-1.9-5.2c0-4.4 3.6-8 8-8l66.1.3L512 464.6l99.3-118.4 66-.3c4.4 0 8 3.5 8 8 0 1.9-.7 3.7-1.9 5.2L553.5 514l130 155c1.2 1.5 1.9 3.3 1.9 5.2 0 4.4-3.6 8-8 8z"/></svg>`,
  warning: `<svg viewBox="64 64 896 896" width="1em" height="1em" fill="#faad14"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm-32 232c0-4.4 3.6-8 8-8h48c4.4 0 8 3.6 8 8v272c0 4.4-3.6 8-8 8h-48c-4.4 0-8-3.6-8-8V296zm32 440a48.01 48.01 0 010-96 48.01 48.01 0 010 96z"/></svg>`,
  info: `<svg viewBox="64 64 896 896" width="1em" height="1em" fill="#1890ff"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm32 664c0 4.4-3.6 8-8 8h-48c-4.4 0-8-3.6-8-8V456c0-4.4 3.6-8 8-8h48c4.4 0 8 3.6 8 8v272zm-32-344a48.01 48.01 0 010-96 48.01 48.01 0 010 96z"/></svg>`,
}

const BG_COLORS: Record<MessageType, string> = {
  success: '#f6ffed',
  error: '#fff2f0',
  warning: '#fffbe6',
  info: '#e6f4ff',
}

const BORDER_COLORS: Record<MessageType, string> = {
  success: '#b7eb8f',
  error: '#ffccc7',
  warning: '#ffe58f',
  info: '#91caff',
}

let container: HTMLDivElement | null = null

function ensureContainer() {
  if (container && document.body.contains(container)) return container
  container = document.createElement('div')
  container.id = 'app-message-container'
  Object.assign(container.style, {
    position: 'fixed',
    top: '24px',
    left: '50%',
    transform: 'translateX(-50%)',
    zIndex: '99999',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    pointerEvents: 'none',
  })
  document.body.appendChild(container)
  return container
}

function show(type: MessageType, content: string, duration = 3000) {
  const ct = ensureContainer()

  const el = document.createElement('div')
  el.innerHTML = `
    <span style="display:inline-flex;align-items:center;margin-right:8px;">${ICONS[type]}</span>
    <span>${content}</span>
  `
  Object.assign(el.style, {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '9px 16px',
    background: BG_COLORS[type],
    border: `1px solid ${BORDER_COLORS[type]}`,
    borderRadius: '8px',
    boxShadow: '0 6px 16px rgba(0,0,0,0.08), 0 3px 6px rgba(0,0,0,0.06)',
    fontSize: '14px',
    color: '#333',
    lineHeight: '1.5',
    pointerEvents: 'auto',
    animation: 'msg-slide-down 0.3s ease',
    maxWidth: '480px',
  })

  ct.appendChild(el)

  // 스타일시트 주입 (한번만)
  if (!document.getElementById('app-message-keyframes')) {
    const style = document.createElement('style')
    style.id = 'app-message-keyframes'
    style.textContent = `
      @keyframes msg-slide-down { from { opacity:0; transform:translateY(-12px); } to { opacity:1; transform:translateY(0); } }
      @keyframes msg-slide-up { from { opacity:1; transform:translateY(0); } to { opacity:0; transform:translateY(-12px); } }
    `
    document.head.appendChild(style)
  }

  setTimeout(() => {
    el.style.animation = 'msg-slide-up 0.3s ease forwards'
    setTimeout(() => el.remove(), 300)
  }, duration)
}

export const message = {
  success: (content: string, duration?: number) => show('success', content, duration),
  error: (content: string, duration?: number) => show('error', content, duration),
  warning: (content: string, duration?: number) => show('warning', content, duration),
  info: (content: string, duration?: number) => show('info', content, duration),
}
