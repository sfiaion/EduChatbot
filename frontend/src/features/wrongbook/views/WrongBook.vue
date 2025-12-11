<template>
  <div style="padding:12px 20px; max-width:960px; margin:0 auto;">
    <h2 class="title-gradient-violet" style="margin:0 0 8px;">错题本</h2>
    <div style="margin-bottom:12px;">
      <el-select v-model="groupBy" style="width:200px;">
        <el-option label="按时间" value="time" />
        <el-option label="按难度" value="difficulty" />
        <el-option label="按函数类型" value="type" />
        <el-option label="按函数性质" value="property" />
      </el-select>
      <el-button style="margin-left:8px;" @click="fetch">刷新</el-button>
    </div>
    <el-table :data="items" stripe style="width:100%;">
      <el-table-column prop="question_id" label="题目ID" width="100" />
      <el-table-column label="题干">
        <template #default="scope">
          <LatexText :content="scope.row.question" />
        </template>
      </el-table-column>
      <el-table-column label="我的错误答案" width="220">
        <template #default="scope">
          <LatexText :content="scope.row.student_answer" />
        </template>
      </el-table-column>
      <el-table-column prop="error_count" label="错误次数" width="120" />
      <el-table-column prop="last_error_time" label="最近错误时间" width="180" />
      <el-table-column label="操作" width="220">
        <template #default="scope">
          <el-button size="small" type="primary" @click="redo(scope.row.question_id)">重做</el-button>
          <el-button size="small" style="margin-left:6px;" @click="remove(scope.row.question_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getWrongbook } from '../../../services/modules/wrongbook'
import { usePracticeStore } from '../../practice/store'
import LatexText from '../../../components/LatexText.vue'
import { ElMessage } from 'element-plus'

const studentId = 1
const groupBy = ref('time')
const items = ref<any[]>([])
const store = usePracticeStore()

onMounted(async () => {
  await store.init(studentId)
  fetch()
})

async function fetch() {
  try {
    items.value = await getWrongbook(studentId, groupBy.value)
  } catch { ElMessage.error('加载失败') }
}
async function redo(qid: number) { await store.add(qid); ElMessage.success('已加入练习清单'); }
function remove(qid: number) { items.value = items.value.filter(i => i.question_id !== qid) }
</script>
