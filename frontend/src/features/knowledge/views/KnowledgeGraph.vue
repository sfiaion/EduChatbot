<template>
  <div class="page-wrap">
    <div class="toolbar card-soft">
      <div class="toolbar-left">
        <h2 class="title-gradient-teal" style="margin:0;">数据分析</h2>
      </div>
      <div class="toolbar-right controls">
        <el-select v-model="classId" placeholder="选择班级" style="width:180px" @change="refreshAll">
          <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width:280px"
          @change="refreshAll"
        />
        <el-autocomplete
          v-model="center"
          :fetch-suggestions="querySearch"
          placeholder="搜索中心知识点"
          style="width:280px"
          @select="onCenterSelect"
        />
        <el-button type="primary" class="ripple" @click="loadGraph">加载图谱</el-button>
        <el-button class="ripple" @click="resetView">重置视图</el-button>
      </div>
    </div>

    <div class="grid">
      <el-card class="card-soft" shadow="always">
        <template #header>知识图谱</template>
        <div ref="graphRef" class="graph-canvas"></div>
      </el-card>

      <div class="side">
        <el-card class="card-soft" shadow="hover">
          <template #header>异常错误增长点</template>
          <div v-if="loadingBreakpoints" class="loading">加载中...</div>
          <div v-else-if="breakpoints.length===0" class="empty">暂无数据</div>
          <div v-else class="list">
            <div v-for="bp in breakpoints" :key="bp.name" class="item">
              <div class="info">
                <span class="name">{{ bp.name }}</span>
                <el-tag type="danger" size="small">差值 {{ bp.diff }}</el-tag>
              </div>
              <div class="ops">
                <el-button size="small" type="primary" @click="setCenter(bp.name)">设为中心</el-button>
                <el-button size="small" @click="openNode(bp.name)">查看</el-button>
              </div>
            </div>
          </div>
        </el-card>
        <el-card class="card-soft" shadow="hover" style="margin-top:12px;">
          <template #header>候选中心知识点</template>
          <div style="display:flex; gap:8px; margin-bottom:8px;">
            <el-input v-model="filter" placeholder="过滤关键字" clearable @input="applyFilter" />
            <el-button size="small" class="ripple" @click="reloadAllNodes">刷新</el-button>
          </div>
          <div v-if="loadingAll" class="loading">加载中...</div>
          <div v-else-if="filtered.length===0" class="empty">暂无候选</div>
          <el-scrollbar v-else height="280px">
            <div class="cand-list">
              <div v-for="n in filtered" :key="n" class="cand-item">
                <span>{{ n }}</span>
                <div>
                  <el-button size="small" type="primary" @click="setCenter(n)">设为中心</el-button>
                  <el-button size="small" @click="openNode(n)">查看</el-button>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </div>
    </div>

    <el-drawer v-model="detailVisible" :title="detail?.node.name" size="40%">
      <div v-if="loadingDetail">加载中...</div>
      <div v-else-if="!detail">暂无数据</div>
      <div v-else class="drawer-body">
        <div class="meta">
          <el-tag type="warning">最长前置路径 {{ detail.node.longest_path }}</el-tag>
          <el-tag type="danger">总错误 {{ detail.node.total_errors }}</el-tag>
        </div>
        <div class="content">
          <div class="title">知识点内容</div>
          <LatexText :content="detail.node.content" class="text" />
        </div>
        <div class="chart">
          <div class="title">每日错误趋势</div>
          <div ref="chartRef" style="height:260px;"></div>
        </div>
        <div class="preceding">
          <div class="title">高频前置节点</div>
          <div class="tags">
            <el-tag v-for="p in detail.preceding_nodes" :key="p.name" effect="plain" type="info" style="margin-right:8px; margin-bottom:8px;">
              {{ p.name }} / {{ p.total_errors }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Graph } from '@antv/g6'
import * as echarts from 'echarts'
import { getTeacherClasses } from '../../../services/modules/teacher'
import { searchKnowledgeNodes, getKnowledgeSubgraph, getBreakpoints, getNodeAnalysis, listAllKnowledgeNodes, getCandidateNodes } from '../../../services/modules/knowledge'
import LatexText from '../../../components/LatexText.vue'

const classes = ref<Array<{ id: number; name: string }>>([])
const classId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const center = ref('')

const graphRef = ref<HTMLElement>()
let graph: Graph | null = null

const loadingBreakpoints = ref(false)
const breakpoints = ref<Array<{ name: string; diff: number }>>([])

const loadingAll = ref(false)
const allNodes = ref<string[]>([])
const filter = ref('')
const filtered = ref<string[]>([])

const detailVisible = ref(false)
const loadingDetail = ref(false)
const detail = ref<{
  node: { name: string; total_errors: number; daily_errors: Record<string, number>; content: string; longest_path: number }
  preceding_nodes: Array<{ name: string; total_errors: number }>
} | null>(null)
const chartRef = ref<HTMLElement>()
let lineChart: echarts.ECharts | null = null

onMounted(async () => {
  await loadClasses()
  initDefaults()
  await refreshBreakpoints()
  await reloadAllNodes()
})

function initDefaults() {
  const today = new Date()
  const end = formatDate(today)
  const startDate = new Date(today.getTime() - 6 * 24 * 3600 * 1000)
  const start = formatDate(startDate)
  dateRange.value = [start, end]
}

async function loadClasses() {
  try {
    const list = await getTeacherClasses()
    classes.value = list
    const first = list[0]
    if (first && !classId.value) classId.value = first.id
  } catch {
    ElMessage.error('获取班级失败')
  }
}

function formatDate(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function querySearch(q: string, cb: (res: Array<{ value: string }>) => void) {
  if (!q) return cb([])
  try {
    const list = await searchKnowledgeNodes(q)
    cb(list.map(i => ({ value: i.name })))
  } catch {
    cb([])
  }
}

function onCenterSelect(i: { value: string }) {
  center.value = i.value
  loadGraph()
}

async function refreshBreakpoints() {
  if (!classId.value || !dateRange.value) return
  loadingBreakpoints.value = true
  try {
    breakpoints.value = await getBreakpoints(classId.value, dateRange.value[0], dateRange.value[1], 5)
  } catch {
    ElMessage.error('加载断点失败')
  } finally {
    loadingBreakpoints.value = false
  }
}

function refreshAll() {
  refreshBreakpoints()
  reloadAllNodes()
}

function setCenter(name: string) {
  center.value = name
  loadGraph()
}

function resetView() {
  if (graph) graph.fitView()
}

async function loadGraph() {
  if (!center.value) {
    ElMessage.warning('请输入中心知识点')
    return
  }
  try {
    const data = await getKnowledgeSubgraph(center.value)
    await nextTick()
    const nodes = data.nodes.map(n => ({ id: n.id, label: n.label, style: { fill: n.id === center.value ? '#16a34a' : '#60a5fa', stroke: '#2563eb' } }))
    const edges = data.edges.map((e, idx) => ({ id: `e-${idx}`, source: e.source, target: e.target }))
    if (graph) {
      graph.destroy()
    }
    graph = new Graph({
      container: graphRef.value as HTMLElement,
      width: (graphRef.value as HTMLElement).clientWidth,
      height: 520,
      autoFit: 'view',
      layout: { type: 'force' },
      behaviors: ['drag-canvas', 'drag-node', 'zoom-canvas'],
      theme: 'light',
      data: { nodes, edges }
    })
    graph.on('node:click', (ev: any) => {
      const id = ev?.itemId || ev?.id || ev?.target?.id
      if (id) openNode(String(id))
    })
    graph.render()
    graph.fitView()
  } catch {
    ElMessage.error('加载图谱失败')
  }
}

async function openNode(name: string) {
  if (!classId.value || !dateRange.value) {
    ElMessage.warning('请选择班级与时间范围')
    return
  }
  detailVisible.value = true
  loadingDetail.value = true
  try {
    const r = await getNodeAnalysis(name, classId.value, dateRange.value[0], dateRange.value[1])
    detail.value = r
    await nextTick()
    if (chartRef.value) {
      lineChart = echarts.init(chartRef.value)
      const keys = Object.keys(r.node.daily_errors).sort()
      const vals = keys.map(k => r.node.daily_errors[k] || 0)
      lineChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: keys },
        yAxis: { type: 'value' },
        series: [{ type: 'line', data: vals, smooth: true }]
      })
    }
  } catch {
    ElMessage.error('加载节点详情失败')
  } finally {
    loadingDetail.value = false
  }
}

async function reloadAllNodes() {
  loadingAll.value = true
  try {
    if (classId.value && dateRange.value) {
      const list = await getCandidateNodes(classId.value, dateRange.value[0], dateRange.value[1], 100)
      allNodes.value = list
    } else {
      const list = await listAllKnowledgeNodes(1000)
      allNodes.value = list.map(i => i.name)
    }
    applyFilter()
  } catch {
    ElMessage.error('加载候选知识点失败')
  } finally {
    loadingAll.value = false
  }
}

function applyFilter() {
  const q = (filter.value || '').trim().toLowerCase()
  filtered.value = !q ? allNodes.value : allNodes.value.filter(n => n.toLowerCase().includes(q))
}
</script>
<style scoped>
.page-wrap { padding: 16px; }
.toolbar { padding: 12px; margin-bottom: 12px; display:flex; align-items:center; justify-content:space-between; }
.controls { display:flex; align-items:center; gap:10px; }
.grid { display:grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.graph-canvas { height: 520px; }
.side .list { display: grid; gap: 10px; }
.side .item { display:flex; align-items:center; justify-content:space-between; padding:8px; border:1px solid var(--border-soft); border-radius:8px; }
.side .name { font-weight:600; color:#374151; }
.cand-list { display:grid; gap:8px; }
.cand-item { display:flex; align-items:center; justify-content:space-between; padding:6px; border:1px dashed var(--border-soft); border-radius:8px; }
.drawer-body { display:grid; gap:14px; }
.meta { display:flex; gap:8px; align-items:center; }
.content .title, .chart .title, .preceding .title { font-weight:600; color:#374151; margin-bottom:6px; }
.content .text { font-size:14px; color:#4b5563; }
</style>
