<template>
  <div class="gis-page">
    <div class="page-header">
      <h2><EnvironmentOutlined /> 공간정보 조회</h2>
      <p v-if="linkedDataset">
        <span class="linked-badge">연동 데이터셋: <strong>{{ linkedDataset }}</strong></span>
        — 해당 데이터의 공간정보를 지도에서 시각화합니다.
      </p>
      <p v-else>K-water 시설물의 공간 데이터를 지도에서 조회합니다.</p>
    </div>

    <div class="gis-body">
      <!-- 좌측 패널 -->
      <aside class="layer-panel">
        <!-- 베이스맵 선택 -->
        <div class="panel-section">
          <div class="panel-header"><GlobalOutlined /> 베이스맵</div>
          <div class="basemap-list">
            <label
              v-for="bm in basemaps"
              :key="bm.id"
              class="basemap-item"
              :class="{ active: currentBasemap === bm.id }"
            >
              <input type="radio" name="basemap" :value="bm.id" v-model="currentBasemap" @change="changeBasemap(bm.id)" />
              <span class="basemap-thumb" :style="{ backgroundImage: `url(${bm.thumb})` }">
                <span class="basemap-icon">{{ bm.icon }}</span>
              </span>
              <span class="basemap-name">{{ bm.name }}</span>
            </label>
          </div>
        </div>

        <!-- 레이어 목록 -->
        <div class="panel-section">
          <div class="panel-header"><AppstoreOutlined /> 레이어</div>
          <div class="layer-list">
            <div v-for="layer in layers" :key="layer.id" class="layer-item-wrap">
              <label class="layer-item" :class="{ active: layer.visible }">
                <input type="checkbox" v-model="layer.visible" @change="toggleLayer(layer)" />
                <span class="layer-color" :style="{ background: layer.color }"></span>
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-count">{{ layer.features.length }}</span>
                <button class="style-toggle-btn" @click.prevent.stop="toggleStylePanel(layer.id)" :title="'스타일 설정'">
                  <SettingOutlined />
                </button>
              </label>
              <!-- 인라인 스타일 설정 패널 -->
              <div v-if="expandedStyleLayer === layer.id" class="style-panel-inline">
                <div class="style-section">
                  <div class="style-row">
                    <label>내부 색상</label>
                    <input type="color" :value="getLayerStyle(layer.id).fillColor" @input="updateLayerStyle(layer.id, 'fillColor', ($event.target as HTMLInputElement).value)" />
                  </div>
                  <div class="style-row">
                    <label>테두리 색상</label>
                    <input type="color" :value="getLayerStyle(layer.id).strokeColor" @input="updateLayerStyle(layer.id, 'strokeColor', ($event.target as HTMLInputElement).value)" />
                  </div>
                  <div class="style-row" v-if="layer.type === 'point'">
                    <label>심볼 크기</label>
                    <input type="range" min="4" max="20" :value="getLayerStyle(layer.id).radius" @input="updateLayerStyle(layer.id, 'radius', Number(($event.target as HTMLInputElement).value))" />
                    <span class="range-val">{{ getLayerStyle(layer.id).radius }}px</span>
                  </div>
                  <div class="style-row" v-if="layer.type === 'point'">
                    <label>테두리 두께</label>
                    <input type="range" min="0" max="6" :value="getLayerStyle(layer.id).strokeWidth" @input="updateLayerStyle(layer.id, 'strokeWidth', Number(($event.target as HTMLInputElement).value))" />
                    <span class="range-val">{{ getLayerStyle(layer.id).strokeWidth }}px</span>
                  </div>
                  <div class="style-row" v-if="layer.type === 'line'">
                    <label>선 두께</label>
                    <input type="range" min="1" max="10" :value="getLayerStyle(layer.id).strokeWidth" @input="updateLayerStyle(layer.id, 'strokeWidth', Number(($event.target as HTMLInputElement).value))" />
                    <span class="range-val">{{ getLayerStyle(layer.id).strokeWidth }}px</span>
                  </div>
                </div>
                <!-- 레이블 텍스트 스타일 (포인트만) -->
                <div class="style-section" v-if="layer.type === 'point'">
                  <div class="style-section-title">레이블 텍스트</div>
                  <div class="style-row">
                    <label>표시</label>
                    <input type="checkbox" :checked="getLayerStyle(layer.id).labelVisible" @change="updateLayerStyle(layer.id, 'labelVisible', ($event.target as HTMLInputElement).checked)" />
                  </div>
                  <div class="style-row">
                    <label>글자 색상</label>
                    <input type="color" :value="getLayerStyle(layer.id).labelColor" @input="updateLayerStyle(layer.id, 'labelColor', ($event.target as HTMLInputElement).value)" />
                  </div>
                  <div class="style-row">
                    <label>글자 크기</label>
                    <input type="range" min="8" max="24" :value="getLayerStyle(layer.id).labelFontSize" @input="updateLayerStyle(layer.id, 'labelFontSize', Number(($event.target as HTMLInputElement).value))" />
                    <span class="range-val">{{ getLayerStyle(layer.id).labelFontSize }}px</span>
                  </div>
                  <div class="style-row">
                    <label>위치</label>
                    <select :value="getLayerStyle(layer.id).labelPosition" @change="updateLayerStyle(layer.id, 'labelPosition', ($event.target as HTMLSelectElement).value)">
                      <option value="top">위</option>
                      <option value="bottom">아래</option>
                      <option value="left">왼쪽</option>
                      <option value="right">오른쪽</option>
                    </select>
                  </div>
                  <div class="style-row">
                    <label>헤일로(테두리)</label>
                    <input type="color" :value="getLayerStyle(layer.id).labelHaloColor" @input="updateLayerStyle(layer.id, 'labelHaloColor', ($event.target as HTMLInputElement).value)" />
                  </div>
                </div>
                <div class="style-actions">
                  <button class="reset-btn" @click="resetLayerStyle(layer.id)">초기화</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 속성 정보 -->
        <div class="panel-section" v-if="selectedFeature">
          <div class="panel-header"><InfoCircleOutlined /> 속성 정보</div>
          <div class="feature-info">
            <div v-for="(val, key) in selectedFeature" :key="key" class="info-row">
              <span class="info-key">{{ key }}</span>
              <span class="info-val">{{ val }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section" v-if="!selectedFeature">
          <div class="panel-header"><InfoCircleOutlined /> 안내</div>
          <div class="hint-text">지도에서 시설물을 클릭하면 속성 정보가 표시됩니다.</div>
        </div>
      </aside>

      <!-- 지도 영역 -->
      <div class="map-container">
        <div ref="mapRef" class="ol-map"></div>
        <div class="map-controls">
          <button class="map-btn" @click="zoomToKorea" title="전체보기"><AimOutlined /></button>
          <button class="map-btn gallery-upload-btn" @click="openGalleryPublishModal" title="시각화 갤러리에 올리기"><UploadOutlined /></button>
        </div>

        <!-- 갤러리 게시 모달 -->
        <div v-if="showPublishModal" class="gis-publish-overlay" @click.self="showPublishModal = false">
          <div class="gis-publish-modal">
            <div class="gis-publish-header">
              <UploadOutlined /> 시각화 갤러리에 올리기
              <button class="gis-publish-close" @click="showPublishModal = false"><CloseOutlined /></button>
            </div>
            <div class="gis-publish-body">
              <div class="gis-publish-field">
                <label>차트 이름</label>
                <input v-model="publishForm.name" placeholder="갤러리에 표시될 이름" />
              </div>
              <div class="gis-publish-field">
                <label>설명</label>
                <textarea v-model="publishForm.description" rows="2" placeholder="지도에 대한 설명 (선택)"></textarea>
              </div>
              <div class="gis-publish-preview">
                <label>포함될 레이어</label>
                <div class="preview-layers">
                  <span v-for="l in layers.filter(x => x.visible)" :key="l.id" class="preview-layer-tag">
                    <span class="tag-dot" :style="{ background: getLayerStyle(l.id).fillColor }"></span>
                    {{ l.name }} ({{ l.features.length }})
                  </span>
                </div>
              </div>
            </div>
            <div class="gis-publish-footer">
              <button class="btn btn-primary" @click="confirmPublishToGallery"><UploadOutlined /> 갤러리에 올리기</button>
              <button class="btn btn-outline" @click="showPublishModal = false">취소</button>
            </div>
          </div>
        </div>
        <div class="map-legend">
          <span v-for="layer in layers.filter(l => l.visible)" :key="layer.id" class="legend-item">
            <span class="legend-dot" :style="{ background: getLayerStyle(layer.id).fillColor }"></span>
            {{ layer.name }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { EnvironmentOutlined, AppstoreOutlined, InfoCircleOutlined, AimOutlined, GlobalOutlined, SettingOutlined, UploadOutlined, CloseOutlined } from '@ant-design/icons-vue'
import { visualizationApi } from '../../api/portal.api'

// OpenLayers
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import XYZ from 'ol/source/XYZ'
import GeoJSON from 'ol/format/GeoJSON'
import { Style, Fill, Stroke, Circle as CircleStyle, Text as TextStyle } from 'ol/style'
import { fromLonLat } from 'ol/proj'
import 'ol/ol.css'

const route = useRoute()
const mapRef = ref<HTMLElement>()
let map: Map | null = null
let baseLayer: TileLayer<XYZ> | null = null
const selectedFeature = ref<Record<string, any> | null>(null)
const linkedDatasetId = computed(() => route.query.dataset_id ? String(route.query.dataset_id) : null)
const linkedDatasetNameKr = computed(() => route.query.name_kr ? String(route.query.name_kr) : null)
const linkedDatasetName = computed(() => route.query.name ? String(route.query.name) : null)
// "한글명 (ID)" 형식으로 표시
const linkedDataset = computed(() => {
  const kr = linkedDatasetNameKr.value
  const en = linkedDatasetName.value
  const id = linkedDatasetId.value
  if (kr && id) return `${kr} (${id})`
  if (kr) return kr
  if (en && id) return `${en} (${id})`
  if (en) return en
  if (id) return id
  return null
})
const expandedStyleLayer = ref<string | null>(null)

// ── 베이스맵 정의 ──
const basemaps = [
  { id: 'standard', name: '표준', icon: '🗺', thumb: '', url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}' },
  { id: 'satellite', name: '위성', icon: '🛰', thumb: '', url: 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}' },
  { id: 'hybrid', name: '하이브리드', icon: '🌐', thumb: '', url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' },
  { id: 'terrain', name: '지형', icon: '⛰', thumb: '', url: 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}' },
  { id: 'midnight', name: '미드나이트', icon: '🌙', thumb: '', url: 'https://{a-c}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png' },
  { id: 'light', name: '라이트', icon: '☀', thumb: '', url: 'https://{a-c}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png' },
]
const currentBasemap = ref('standard')

// ── 레이어별 스타일 상태 ──
interface LayerStyleConfig {
  fillColor: string
  strokeColor: string
  strokeWidth: number
  radius: number
  labelVisible: boolean
  labelColor: string
  labelFontSize: number
  labelPosition: 'top' | 'bottom' | 'left' | 'right'
  labelHaloColor: string
}

const defaultLayerStyles: Record<string, LayerStyleConfig> = {
  pipeline: { fillColor: '#1890ff', strokeColor: '#1890ff', strokeWidth: 3, radius: 8, labelVisible: true, labelColor: '#333333', labelFontSize: 12, labelPosition: 'top', labelHaloColor: '#ffffff' },
  plant: { fillColor: '#52c41a', strokeColor: '#ffffff', strokeWidth: 2, radius: 8, labelVisible: true, labelColor: '#333333', labelFontSize: 12, labelPosition: 'top', labelHaloColor: '#ffffff' },
  dam: { fillColor: '#DC3545', strokeColor: '#ffffff', strokeWidth: 2, radius: 8, labelVisible: true, labelColor: '#333333', labelFontSize: 12, labelPosition: 'top', labelHaloColor: '#ffffff' },
  station: { fillColor: '#fa8c16', strokeColor: '#ffffff', strokeWidth: 2, radius: 8, labelVisible: true, labelColor: '#333333', labelFontSize: 12, labelPosition: 'top', labelHaloColor: '#ffffff' },
  quality: { fillColor: '#722ed1', strokeColor: '#ffffff', strokeWidth: 2, radius: 8, labelVisible: true, labelColor: '#333333', labelFontSize: 12, labelPosition: 'top', labelHaloColor: '#ffffff' },
}

const layerStyles: Record<string, LayerStyleConfig> = reactive(
  JSON.parse(JSON.stringify(defaultLayerStyles))
)

function getLayerStyle(layerId: string): LayerStyleConfig {
  return layerStyles[layerId]
}

function toggleStylePanel(layerId: string) {
  expandedStyleLayer.value = expandedStyleLayer.value === layerId ? null : layerId
}

// ── Mock GeoJSON 데이터 ──
const damData = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.8148, 37.9433] }, properties: { name: '소양강댐', type: '다목적댐', capacity: '29억톤', height: '123m', built: '1973' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.9956, 36.9914] }, properties: { name: '충주댐', type: '다목적댐', capacity: '27.5억톤', height: '97.5m', built: '1985' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.9167, 36.5833] }, properties: { name: '안동댐', type: '다목적댐', capacity: '12.5억톤', height: '83m', built: '1976' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.0500, 35.5667] }, properties: { name: '합천댐', type: '다목적댐', capacity: '7.9억톤', height: '96m', built: '1989' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.4833, 36.4736] }, properties: { name: '대청댐', type: '다목적댐', capacity: '14.9억톤', height: '72m', built: '1980' } },
  ]
}

const plantData = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [126.9897, 37.1234] }, properties: { name: '화성정수장', capacity: '30만톤/일', region: '경기도 화성시' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.1189, 36.4568] }, properties: { name: '공주정수장', capacity: '15만톤/일', region: '충남 공주시' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.4870, 36.6356] }, properties: { name: '청주정수장', capacity: '25만톤/일', region: '충북 청주시' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [129.0756, 35.1796] }, properties: { name: '부산정수장', capacity: '40만톤/일', region: '부산광역시' } },
  ]
}

const stationData = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.0015, 37.5642] }, properties: { name: '한강대교 수위관측소', code: 'HN-001', type: '수위' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [126.9667, 37.5439] }, properties: { name: '노량진 수위관측소', code: 'HN-002', type: '수위' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.6000, 35.8700] }, properties: { name: '낙동강 수위관측소', code: 'NK-001', type: '수위' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.3800, 36.3500] }, properties: { name: '금강 수위관측소', code: 'GG-001', type: '수위' } },
  ]
}

const qualityData = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.0300, 37.5100] }, properties: { name: '팔당 수질측정소', grade: '1등급', ph: '7.2', do: '9.5mg/L' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.5000, 36.4800] }, properties: { name: '대청호 수질측정소', grade: '1등급', ph: '7.0', do: '10.1mg/L' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.7200, 35.9300] }, properties: { name: '낙동강 수질측정소', grade: '2등급', ph: '7.4', do: '8.3mg/L' } },
  ]
}

const pipelineData = {
  type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[126.978, 37.566], [126.990, 37.450], [127.000, 37.300], [126.989, 37.124]] }, properties: { name: '서울-화성 상수관로', diameter: '1200mm', length: '48.2km', material: '덕타일주철관' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[127.484, 36.474], [127.400, 36.500], [127.200, 36.520], [127.119, 36.457]] }, properties: { name: '대청-공주 송수관로', diameter: '900mm', length: '35.8km', material: '강관' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[127.484, 36.474], [127.487, 36.636]] }, properties: { name: '대청-청주 송수관로', diameter: '1000mm', length: '18.5km', material: '덕타일주철관' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[128.917, 36.583], [128.800, 36.200], [128.720, 35.930]] }, properties: { name: '안동-낙동강 송수관로', diameter: '800mm', length: '72.1km', material: 'PCCP관' } },
  ]
}

// ── 레이어 정의 ──
const layers = reactive([
  { id: 'pipeline', name: '상수관로', color: '#1890ff', visible: true, features: pipelineData.features, geojson: pipelineData, type: 'line' },
  { id: 'plant', name: '정수장', color: '#52c41a', visible: true, features: plantData.features, geojson: plantData, type: 'point' },
  { id: 'dam', name: '댐', color: '#DC3545', visible: true, features: damData.features, geojson: damData, type: 'point' },
  { id: 'station', name: '수위관측소', color: '#fa8c16', visible: true, features: stationData.features, geojson: stationData, type: 'point' },
  { id: 'quality', name: '수질측정소', color: '#722ed1', visible: true, features: qualityData.features, geojson: qualityData, type: 'point' },
])

const olLayers: Record<string, VectorLayer<VectorSource>> = {}

function getLabelOffset(position: string): [number, number] {
  switch (position) {
    case 'top': return [0, -16]
    case 'bottom': return [0, 16]
    case 'left': return [-16, 0]
    case 'right': return [16, 0]
    default: return [0, -16]
  }
}

function getLabelAlign(position: string): CanvasTextAlign {
  switch (position) {
    case 'left': return 'right'
    case 'right': return 'left'
    default: return 'center'
  }
}

function getLabelBaseline(position: string): CanvasTextBaseline {
  switch (position) {
    case 'top': return 'bottom'
    case 'bottom': return 'top'
    default: return 'middle'
  }
}

function createStyledLayer(layerId: string, layerType: string) {
  const cfg = layerStyles[layerId]
  if (layerType === 'line') {
    return new Style({
      stroke: new Stroke({ color: cfg.fillColor, width: cfg.strokeWidth }),
    })
  }
  const offset = getLabelOffset(cfg.labelPosition)
  return new Style({
    image: new CircleStyle({
      radius: cfg.radius,
      fill: new Fill({ color: cfg.fillColor }),
      stroke: new Stroke({ color: cfg.strokeColor, width: cfg.strokeWidth }),
    }),
    text: cfg.labelVisible
      ? new TextStyle({
          offsetX: offset[0],
          offsetY: offset[1],
          textAlign: getLabelAlign(cfg.labelPosition),
          textBaseline: getLabelBaseline(cfg.labelPosition),
          font: `${cfg.labelFontSize}px Pretendard, sans-serif`,
          fill: new Fill({ color: cfg.labelColor }),
          stroke: new Stroke({ color: cfg.labelHaloColor, width: 3 }),
        })
      : undefined,
  })
}

function refreshLayerStyle(layerId: string) {
  const olLayer = olLayers[layerId]
  if (!olLayer) return
  const layer = layers.find(l => l.id === layerId)
  if (!layer) return

  // 레전드용 layer.color도 동기화
  layer.color = layerStyles[layerId].fillColor

  olLayer.setStyle((feature: any) => {
    const style = createStyledLayer(layerId, layer.type)
    if (layer.type === 'point' && layerStyles[layerId].labelVisible) {
      style.getText()?.setText(feature.get('name') || '')
    }
    return style
  })
}

function updateLayerStyle(layerId: string, key: keyof LayerStyleConfig, value: any) {
  ;(layerStyles[layerId] as any)[key] = value
  refreshLayerStyle(layerId)
}

function resetLayerStyle(layerId: string) {
  Object.assign(layerStyles[layerId], JSON.parse(JSON.stringify(defaultLayerStyles[layerId])))
  refreshLayerStyle(layerId)
}

function changeBasemap(bmId: string) {
  if (!baseLayer) return
  const bm = basemaps.find(b => b.id === bmId)
  if (!bm) return
  baseLayer.setSource(new XYZ({
    url: bm.url,
    maxZoom: 19,
  }))
}

function initMap() {
  if (!mapRef.value) return

  // 베이스맵
  baseLayer = new TileLayer({
    source: new XYZ({
      url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
      maxZoom: 19,
    }),
  })

  // 벡터 레이어 생성
  const vectorLayers: VectorLayer<VectorSource>[] = []
  for (const layer of layers) {
    const source = new VectorSource({
      features: new GeoJSON().readFeatures(layer.geojson, {
        featureProjection: 'EPSG:3857',
      }),
    })
    const olLayer = new VectorLayer({
      source,
      style: (feature) => {
        const style = createStyledLayer(layer.id, layer.type)
        if (layer.type === 'point' && layerStyles[layer.id].labelVisible) {
          style.getText()?.setText(feature.get('name') || '')
        }
        return style
      },
      visible: layer.visible,
    })
    olLayers[layer.id] = olLayer
    vectorLayers.push(olLayer)
  }

  map = new Map({
    target: mapRef.value,
    layers: [baseLayer, ...vectorLayers],
    view: new View({
      center: fromLonLat([127.5, 36.5]),
      zoom: 7,
    }),
  })

  // 클릭 인터랙션
  map.on('click', (evt) => {
    selectedFeature.value = null
    map?.forEachFeatureAtPixel(evt.pixel, (feature) => {
      const props = feature.getProperties()
      const cleaned: Record<string, any> = {}
      for (const [k, v] of Object.entries(props)) {
        if (k !== 'geometry') cleaned[k] = v
      }
      selectedFeature.value = cleaned
      return true
    })
  })

  // 커서 변경
  map.on('pointermove', (evt) => {
    const hit = map?.hasFeatureAtPixel(evt.pixel)
    if (mapRef.value) {
      mapRef.value.style.cursor = hit ? 'pointer' : ''
    }
  })
}

function toggleLayer(layer: any) {
  const olLayer = olLayers[layer.id]
  if (olLayer) {
    olLayer.setVisible(layer.visible)
  }
}

function zoomToKorea() {
  map?.getView().animate({
    center: fromLonLat([127.5, 36.5]),
    zoom: 7,
    duration: 500,
  })
}

// ── 갤러리에 올리기 ──
const showPublishModal = ref(false)
const publishForm = ref({ name: '', description: '' })

function openGalleryPublishModal() {
  const datasetLabel = linkedDataset.value || 'K-water 시설물 공간정보'
  publishForm.value = { name: datasetLabel, description: '' }
  showPublishModal.value = true
}

async function confirmPublishToGallery() {
  const view = map?.getView()
  let center: number[] = [127.5, 36.5]
  try {
    const c = view?.getCenter()
    if (c) {
      const { toLonLat } = await import('ol/proj')
      center = toLonLat(c)
    }
  } catch { /* fallback */ }
  const zoom = view?.getZoom() || 7
  const layerConfigs = layers.map(l => ({
    id: l.id,
    name: l.name,
    visible: l.visible,
    type: l.type,
    style: { ...layerStyles[l.id] },
  }))

  try {
    await visualizationApi.createChart({
      chart_name: publishForm.value.name || 'GIS 지도',
      chart_type: 'MAP',
      chart_config: {
        content_type: 'gis_map',
        basemap: currentBasemap.value,
        center,
        zoom,
        layers: layerConfigs,
        dataset_id: linkedDatasetId.value || null,
        dataset_name: linkedDataset.value || 'K-water 시설물',
        description: publishForm.value.description,
      },
      is_public: true,
    })
    showPublishModal.value = false
    // 성공 알림
    const toast = document.createElement('div')
    toast.className = 'gis-toast gis-toast--success'
    toast.textContent = '시각화 갤러리에 등록되었습니다!'
    document.body.appendChild(toast)
    requestAnimationFrame(() => toast.classList.add('show'))
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300) }, 2500)
  } catch (e) {
    console.error('갤러리 등록 실패:', e)
    const toast = document.createElement('div')
    toast.className = 'gis-toast gis-toast--error'
    toast.textContent = '갤러리 등록에 실패했습니다.'
    document.body.appendChild(toast)
    requestAnimationFrame(() => toast.classList.add('show'))
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300) }, 2500)
  }
}

onMounted(async () => {
  await nextTick()
  initMap()
  // publish=1 쿼리파라미터가 있으면 자동으로 갤러리 게시 모달 열기
  if (route.query.publish === '1') {
    setTimeout(() => openGalleryPublishModal(), 500)
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.gis-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
}

.page-header {
  margin-bottom: 12px;
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: 2px; display: flex; align-items: center; gap: 8px; }
  p { font-size: $font-size-sm; color: $text-muted; margin: 0; }
  .linked-badge { background: #e6f7ff; color: #0066CC; padding: 2px 10px; border-radius: 4px; font-size: 12px; }
}

.gis-body {
  display: flex;
  flex: 1;
  gap: 0;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  overflow: hidden;
  background: $white;
}

// 좌측 레이어 패널
.layer-panel {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: #fafbfc;
}

.panel-section {
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; flex: 1; }
}

.panel-header {
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #333;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  gap: 6px;
}

// ── 베이스맵 선택 ──
.basemap-list {
  padding: 8px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.basemap-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  border: 2px solid transparent;
  font-size: 11px;
  color: #666;

  &:hover { background: #e8f0fe; }
  &.active { border-color: $primary; background: #f0f7ff; color: $primary; font-weight: 600; }

  input[type="radio"] { display: none; }

  .basemap-thumb {
    width: 44px;
    height: 32px;
    border-radius: 4px;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    border: 1px solid #ddd;
  }

  .basemap-name { text-align: center; white-space: nowrap; }
}

// ── 레이어 목록 ──
.layer-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.layer-item-wrap {
  display: flex;
  flex-direction: column;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;

  &:hover { background: #e8f0fe; }
  &.active { background: #f0f7ff; }

  input[type="checkbox"] { accent-color: $primary; }

  .layer-color {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    flex-shrink: 0;
  }

  .layer-name { flex: 1; font-weight: 500; }

  .layer-count {
    font-size: 11px;
    color: #999;
    background: #f0f0f0;
    padding: 1px 6px;
    border-radius: 10px;
  }
}

.style-toggle-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.15s;

  &:hover { color: $primary; background: #e8f0fe; }
}

// ── 인라인 스타일 패널 ──
.style-panel-inline {
  margin: 0 8px 6px 8px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.style-section {
  margin-bottom: 8px;
  &:last-of-type { margin-bottom: 0; }
}

.style-section-title {
  font-size: 11px;
  font-weight: 700;
  color: #666;
  margin-bottom: 6px;
  padding-top: 6px;
  border-top: 1px solid #f0f0f0;
}

.style-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;

  &:last-child { margin-bottom: 0; }

  > label {
    min-width: 70px;
    color: #666;
    font-weight: 500;
    flex-shrink: 0;
  }

  input[type="color"] {
    width: 28px;
    height: 24px;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1px;
    cursor: pointer;
    background: transparent;
  }

  input[type="range"] {
    flex: 1;
    height: 4px;
    accent-color: $primary;
    cursor: pointer;
  }

  input[type="checkbox"] {
    accent-color: $primary;
    width: 16px;
    height: 16px;
  }

  select {
    flex: 1;
    padding: 3px 6px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 12px;
    background: #fff;
    cursor: pointer;

    &:focus { border-color: $primary; outline: none; }
  }

  .range-val {
    min-width: 32px;
    text-align: right;
    color: #999;
    font-size: 11px;
  }
}

.style-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.reset-btn {
  padding: 3px 10px;
  font-size: 11px;
  color: #666;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover { color: $primary; border-color: $primary; background: #f0f7ff; }
}

// 속성 정보
.feature-info {
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  font-size: 12px;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f5f5f5;

  .info-key {
    min-width: 70px;
    color: #999;
    font-weight: 600;
  }
  .info-val {
    flex: 1;
    color: #333;
    font-weight: 500;
    word-break: break-all;
  }
}

.hint-text {
  padding: 14px;
  font-size: 12px;
  color: #999;
  text-align: center;
}

// 지도 영역
.map-container {
  flex: 1;
  position: relative;
}

.ol-map {
  width: 100%;
  height: 100%;
}

.map-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 10;
}

.map-btn {
  width: 36px;
  height: 36px;
  background: $white;
  border: 1px solid $border-color;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #666;
  cursor: pointer;
  box-shadow: $shadow-sm;

  &:hover { background: #f0f7ff; color: $primary; border-color: $primary; }
}

.map-legend {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid $border-color;
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  gap: 14px;
  font-size: 11px;
  color: #666;
  z-index: 10;
  box-shadow: $shadow-sm;

  .legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 3px;
    flex-shrink: 0;
  }
}

// ===== 갤러리 올리기 버튼 =====
.gallery-upload-btn {
  background: #f0f7ff !important;
  color: $primary !important;
  border-color: $primary !important;
}

// ===== 갤러리 게시 모달 =====
.gis-publish-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 9998;
  display: flex; align-items: center; justify-content: center;
}
.gis-publish-modal {
  background: #fff; border-radius: 10px; width: 420px; max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18); overflow: hidden;
}
.gis-publish-header {
  padding: 14px 20px; background: #f5f7fa; border-bottom: 1px solid #e0e0e0;
  font-size: 14px; font-weight: 700; color: #333; display: flex; align-items: center; gap: 8px;
}
.gis-publish-close {
  margin-left: auto; background: none; border: none; color: #999; cursor: pointer;
  font-size: 14px; padding: 2px; border-radius: 4px;
  &:hover { color: #DC3545; background: #fff1f0; }
}
.gis-publish-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.gis-publish-field {
  display: flex; flex-direction: column; gap: 4px;
  label { font-size: 12px; font-weight: 600; color: #666; }
  input, textarea {
    padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 4px;
    font-size: 13px; font-family: inherit;
    &:focus { border-color: $primary; outline: none; }
  }
  textarea { resize: vertical; }
}
.gis-publish-preview {
  label { font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px; display: block; }
  .preview-layers { display: flex; flex-wrap: wrap; gap: 6px; }
  .preview-layer-tag {
    display: flex; align-items: center; gap: 4px; font-size: 11px; color: #333;
    background: #f5f7fa; padding: 3px 8px; border-radius: 4px;
    .tag-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  }
}
.gis-publish-footer {
  padding: 12px 20px; border-top: 1px solid #e0e0e0; display: flex; justify-content: flex-end;
  gap: 8px; background: #fafbfc;
  .btn {
    padding: 7px 16px; font-size: 13px; font-weight: 600; border-radius: 4px;
    cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: all 0.15s;
  }
  .btn-primary { background: $primary; color: #fff; border: 1px solid $primary; &:hover { filter: brightness(0.9); } }
  .btn-outline { background: #fff; color: #666; border: 1px solid #ddd; &:hover { border-color: #999; } }
}

:global(.gis-toast) {
  position: fixed; top: 20px; right: 20px; z-index: 9999; padding: 10px 20px;
  border-radius: 6px; font-size: 13px; font-weight: 600; color: #fff;
  opacity: 0; transform: translateY(-10px); transition: all 0.3s; pointer-events: none;
}
:global(.gis-toast.show) { opacity: 1; transform: translateY(0); }
:global(.gis-toast--success) { background: #28A745; }
:global(.gis-toast--error) { background: #DC3545; }

// OL 기본 컨트롤 스타일 오버라이드
:deep(.ol-control button) {
  background: $white !important;
  color: #333 !important;
  border: 1px solid $border-color !important;
  border-radius: 4px !important;
  font-size: 16px !important;

  &:hover { background: #f0f7ff !important; }
}

:deep(.ol-zoom) {
  top: 12px;
  left: auto;
  right: 12px;
  top: 56px;
}

:deep(.ol-attribution) {
  font-size: 10px;
}
</style>
