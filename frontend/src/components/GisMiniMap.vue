<template>
  <div class="gis-minimap" ref="containerRef">
    <div ref="mapRef" class="minimap-canvas"></div>
    <div class="minimap-overlay" v-if="showOverlayLabel">
      <EnvironmentOutlined /> {{ label || 'GIS 지도' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { EnvironmentOutlined } from '@ant-design/icons-vue'

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

interface LayerStyleCfg {
  fillColor: string
  strokeColor: string
  strokeWidth: number
  radius: number
  labelVisible: boolean
  labelColor: string
  labelFontSize: number
}

const props = defineProps<{
  config: any
  label?: string
  showOverlayLabel?: boolean
  interactive?: boolean
}>()

const containerRef = ref<HTMLElement>()
const mapRef = ref<HTMLElement>()
let map: Map | null = null

// 베이스맵 URL 매핑
const basemapUrls: Record<string, string> = {
  standard: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
  satellite: 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
  hybrid: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
  terrain: 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
  midnight: 'https://{a-c}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  light: 'https://{a-c}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
}

// Mock GeoJSON (GisMap.vue 와 동일 데이터)
const mockGeoData: Record<string, any> = {
  pipeline: { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[126.978, 37.566], [126.990, 37.450], [127.000, 37.300], [126.989, 37.124]] }, properties: { name: '서울-화성 상수관로' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[127.484, 36.474], [127.400, 36.500], [127.200, 36.520], [127.119, 36.457]] }, properties: { name: '대청-공주 송수관로' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[127.484, 36.474], [127.487, 36.636]] }, properties: { name: '대청-청주 송수관로' } },
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[128.917, 36.583], [128.800, 36.200], [128.720, 35.930]] }, properties: { name: '안동-낙동강 송수관로' } },
  ]},
  plant: { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [126.9897, 37.1234] }, properties: { name: '화성정수장' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.1189, 36.4568] }, properties: { name: '공주정수장' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.4870, 36.6356] }, properties: { name: '청주정수장' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [129.0756, 35.1796] }, properties: { name: '부산정수장' } },
  ]},
  dam: { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.8148, 37.9433] }, properties: { name: '소양강댐' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.9956, 36.9914] }, properties: { name: '충주댐' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.9167, 36.5833] }, properties: { name: '안동댐' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.0500, 35.5667] }, properties: { name: '합천댐' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.4833, 36.4736] }, properties: { name: '대청댐' } },
  ]},
  station: { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.0015, 37.5642] }, properties: { name: '한강대교 수위관측소' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [126.9667, 37.5439] }, properties: { name: '노량진 수위관측소' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.6000, 35.8700] }, properties: { name: '낙동강 수위관측소' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.3800, 36.3500] }, properties: { name: '금강 수위관측소' } },
  ]},
  quality: { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.0300, 37.5100] }, properties: { name: '팔당 수질측정소' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [127.5000, 36.4800] }, properties: { name: '대청호 수질측정소' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [128.7200, 35.9300] }, properties: { name: '낙동강 수질측정소' } },
  ]},
}

const defaultColors: Record<string, string> = {
  pipeline: '#1890ff', plant: '#52c41a', dam: '#DC3545', station: '#fa8c16', quality: '#722ed1',
}

const layerTypes: Record<string, string> = {
  pipeline: 'line', plant: 'point', dam: 'point', station: 'point', quality: 'point',
}

function initMap() {
  if (!mapRef.value) return
  const cfg = props.config || {}
  const bmKey = cfg.basemap || 'standard'
  const bmUrl = basemapUrls[bmKey] || basemapUrls.standard
  const center = cfg.center || [127.5, 36.5]
  const zoom = cfg.zoom || 7

  const base = new TileLayer({
    source: new XYZ({ url: bmUrl, maxZoom: 19 }),
  })

  const vectorLayers: VectorLayer<VectorSource>[] = []
  const layersCfg = cfg.layers || Object.keys(mockGeoData).map(id => ({ id, visible: true }))

  for (const lCfg of layersCfg) {
    if (!lCfg.visible) continue
    const geoData = mockGeoData[lCfg.id]
    if (!geoData) continue

    const source = new VectorSource({
      features: new GeoJSON().readFeatures(geoData, { featureProjection: 'EPSG:3857' }),
    })

    const styleCfg: LayerStyleCfg = lCfg.style || {}
    const fillColor = styleCfg.fillColor || defaultColors[lCfg.id] || '#1890ff'
    const strokeColor = styleCfg.strokeColor || '#ffffff'
    const strokeWidth = styleCfg.strokeWidth || (layerTypes[lCfg.id] === 'line' ? 3 : 2)
    const radius = styleCfg.radius || 7

    let style: Style
    if (layerTypes[lCfg.id] === 'line') {
      style = new Style({ stroke: new Stroke({ color: fillColor, width: strokeWidth }) })
    } else {
      style = new Style({
        image: new CircleStyle({
          radius,
          fill: new Fill({ color: fillColor }),
          stroke: new Stroke({ color: strokeColor, width: strokeWidth }),
        }),
        text: (styleCfg.labelVisible !== false)
          ? new TextStyle({
              offsetY: -12,
              font: `${styleCfg.labelFontSize || 10}px Pretendard, sans-serif`,
              fill: new Fill({ color: styleCfg.labelColor || '#333' }),
              stroke: new Stroke({ color: '#fff', width: 2 }),
            })
          : undefined,
      })
    }

    const olLayer = new VectorLayer({
      source,
      style: (feature) => {
        if (layerTypes[lCfg.id] === 'point' && styleCfg.labelVisible !== false) {
          const s = style.clone()
          s.getText()?.setText(feature.get('name') || '')
          return s
        }
        return style
      },
    })
    vectorLayers.push(olLayer)
  }

  map = new Map({
    target: mapRef.value,
    layers: [base, ...vectorLayers],
    view: new View({
      center: fromLonLat(center),
      zoom,
    }),
    controls: [],
    interactions: props.interactive !== false
      ? undefined
      : [],
  })
}

function destroyMap() {
  if (map) {
    map.setTarget(undefined)
    map = null
  }
}

// 부모 사이즈가 바뀌면 맵도 리사이즈
const resizeObserver = ref<ResizeObserver | null>(null)

onMounted(async () => {
  await nextTick()
  initMap()

  if (containerRef.value) {
    resizeObserver.value = new ResizeObserver(() => {
      map?.updateSize()
    })
    resizeObserver.value.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver.value?.disconnect()
  destroyMap()
})

watch(() => props.config, () => {
  destroyMap()
  nextTick(() => initMap())
}, { deep: true })
</script>

<style lang="scss" scoped>
.gis-minimap {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 4px;
}

.minimap-canvas {
  width: 100%;
  height: 100%;
}

.minimap-overlay {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(255, 255, 255, 0.88);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #333;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  pointer-events: none;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
