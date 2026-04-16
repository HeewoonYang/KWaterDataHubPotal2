<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-container" :class="sizeClass">
        <!-- Header -->
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button class="modal-close" @click="$emit('close')"><CloseOutlined /></button>
        </div>
        <!-- Body -->
        <div class="modal-body">
          <slot />
        </div>
        <!-- Footer -->
        <div class="modal-footer" v-if="$slots.footer">
          <slot name="footer" />
        </div>
        <div class="modal-footer" v-else>
          <button class="btn btn-outline" @click="$emit('close')">닫기</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CloseOutlined } from '@ant-design/icons-vue'

const props = defineProps<{
  visible: boolean
  title: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}>()

defineEmits(['close'])

const sizeClass = computed(() => `modal-${props.size || 'lg'}`)
</script>

<style lang="scss">
@use '../styles/variables' as *;

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-container {
  background: $white;
  border-radius: $radius-lg;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  animation: slideUp 0.25s;

  &.modal-sm { width: 480px; }
  &.modal-md { width: 640px; }
  &.modal-lg { width: 900px; }
  &.modal-xl { width: 1100px; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px $spacing-xl;
  background: #2c3e6b;
  border-radius: $radius-lg $radius-lg 0 0;

  h3 { font-size: $font-size-md; font-weight: 600; color: #fff; margin: 0; }
  .modal-close {
    width: 28px; height: 28px; border-radius: 50%; background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center; font-size: 14px;
    color: #fff; transition: all 0.2s;
    &:hover { background: rgba(255,255,255,0.3); }
  }
}

.modal-body {
  padding: $spacing-xl;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-xl $spacing-lg;
  border-top: 1px solid $border-color;
  background: #f0f2f5;
  border-radius: 0 0 $radius-lg $radius-lg;
}

/* 모달 내부 공통 스타일 */
.modal-stats {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
}

.modal-stat-card {
  flex: 1;
  padding: $spacing-md;
  border-radius: $radius-md;
  text-align: center;
  border: 1px solid $border-color;
  background: $white;

  .stat-title { font-size: $font-size-xs; color: $text-muted; margin-bottom: 4px; }
  .stat-number { font-size: $font-size-xl; font-weight: 700; }

  &.primary { border-color: #0066CC; .stat-number { color: #0066CC; } }
  &.success { border-color: #28A745; .stat-number { color: #28A745; } }
  &.warning { border-color: #FFC107; .stat-number { color: #e65100; } }
  &.danger { border-color: #DC3545; .stat-number { color: #DC3545; } }
  &.muted { background: #f5f5f5; .stat-number { color: $text-muted; } }
}

.modal-section {
  margin-bottom: $spacing-lg;

  &-title {
    font-size: $font-size-md;
    font-weight: 600;
    padding-bottom: $spacing-sm;
    margin-bottom: $spacing-md;
    border-left: 3px solid $primary;
    padding-left: $spacing-sm;
    color: $text-primary;
  }
}

.modal-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-sm $spacing-xl;
}

.modal-info-item {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-sm 0;
  border-bottom: 1px solid #f5f5f5;

  .info-label {
    min-width: 100px;
    font-size: $font-size-sm;
    color: $text-muted;
    font-weight: 500;
  }
  .info-value {
    font-size: $font-size-sm;
    color: $text-primary;
    font-weight: 600;
  }
}

.modal-chart-row {
  display: flex;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;

  .chart-panel {
    flex: 1;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    padding: $spacing-md;
    background: $white;

    .chart-title { font-size: $font-size-sm; font-weight: 600; margin-bottom: $spacing-sm; }
    .chart-placeholder { height: 180px; background: #f9fafb; border-radius: $radius-sm; display: flex; align-items: center; justify-content: center; color: $text-muted; font-size: $font-size-sm; }
  }
}

.modal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: $font-size-sm;

  th {
    background: #4a6a8a; color: #fff; padding: 8px 12px; text-align: left;
    font-weight: 600; font-size: 12px;
  }
  td {
    padding: 8px 12px; border-bottom: 1px solid #f0f0f0;
  }
  tr:hover td { background: #f8fafc; }
  .text-right { text-align: right; }
  .text-center { text-align: center; }
}

/* 모달 폼 스타일 */
.modal-form {
  display: flex;
  flex-direction: column;
  gap: 0;

  .form-row {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #e8e8e8;

    &:first-child { border-top: 1px solid #e8e8e8; }

    label {
      min-width: 110px;
      width: 110px;
      padding: 10px 14px;
      font-size: $font-size-sm;
      font-weight: 600;
      color: $text-secondary;
      background: #f5f7fa;
      border-right: 1px solid #e8e8e8;
      border-left: 1px solid #e8e8e8;
      flex-shrink: 0;
      align-self: stretch;
      display: flex;
      align-items: center;
    }

    input, select {
      flex: 1;
      padding: 9px 12px;
      border: none;
      border-right: 1px solid #e8e8e8;
      font-size: $font-size-sm;
      font-family: inherit;
      outline: none;
      background: $white;
      &:focus { background: #f0f7ff; }
    }

    textarea {
      flex: 1;
      padding: 9px 12px;
      border: none;
      border-right: 1px solid #e8e8e8;
      font-size: $font-size-sm;
      font-family: inherit;
      outline: none;
      resize: vertical;
      min-height: 60px;
      background: $white;
      &:focus { background: #f0f7ff; }
    }
  }
}

.modal-form-group {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;

  label {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-secondary;
    &.required::after { content: ' *'; color: #DC3545; }
  }
  input, select, textarea {
    padding: 8px 12px;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    font-size: $font-size-sm;
    font-family: inherit;
    outline: none;
    &:focus { border-color: $primary; box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1); }
  }
}

.modal-form-row {
  display: flex;
  gap: $spacing-lg;
  .modal-form-group { flex: 1; }
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;

  &.badge-success { background: #e8f5e9; color: #2e7d32; }
  &.badge-warning { background: #fff8e1; color: #e65100; }
  &.badge-danger { background: #ffebee; color: #c62828; }
  &.badge-info { background: #e3f2fd; color: #1565c0; }
  &.badge-muted { background: #f5f5f5; color: #757575; }
}

/* 탭 바 스타일 (첨부 디자인 참조) */
.modal-tabs {
  display: flex;
  border-bottom: 2px solid #ddd;
  margin-bottom: $spacing-md;
  gap: 0;

  .modal-tab {
    padding: 8px 18px;
    font-size: $font-size-sm;
    font-weight: 500;
    color: $text-secondary;
    border: 1px solid #ddd;
    border-bottom: none;
    background: #f5f5f5;
    margin-bottom: -2px;
    cursor: pointer;
    border-radius: 4px 4px 0 0;
    transition: all 0.2s;

    &.active {
      background: #3a5998;
      color: #fff;
      border-color: #3a5998;
      font-weight: 600;
    }
    &:hover:not(.active) {
      background: #e8edf3;
    }
  }
}

/* 하단 상세 패널 (첨부 디자인 - 일반/변경이력/UDP/코드 영역) */
.modal-detail-panel {
  border: 1px solid $border-color;
  border-radius: $radius-md;
  margin-top: $spacing-md;
  overflow: hidden;

  .detail-panel-tabs {
    display: flex;
    border-bottom: 1px solid $border-color;
    gap: 0;

    .panel-tab {
      padding: 6px 16px;
      font-size: 12px;
      font-weight: 500;
      color: $text-secondary;
      background: #f0f2f5;
      border-right: 1px solid $border-color;
      cursor: pointer;
      transition: all 0.2s;

      &.active {
        background: #3a5998;
        color: #fff;
        font-weight: 600;
      }
      &:hover:not(.active) { background: #e0e4ea; }
    }
  }

  .detail-panel-body {
    padding: $spacing-md;
    min-height: 120px;
  }
}

/* 키-값 수평 폼 (첨부 디자인 하단 패널 스타일) */
.modal-kv-form {
  display: grid;
  grid-template-columns: 80px 1fr 80px 1fr;
  gap: $spacing-xs $spacing-sm;
  font-size: $font-size-sm;

  .kv-label {
    background: #f5f7fa;
    padding: 6px 8px;
    font-weight: 600;
    color: $text-secondary;
    border: 1px solid #e8e8e8;
    display: flex;
    align-items: center;
  }
  .kv-value {
    padding: 6px 8px;
    border: 1px solid #e8e8e8;
    display: flex;
    align-items: center;
    color: $text-primary;
  }
}
</style>
