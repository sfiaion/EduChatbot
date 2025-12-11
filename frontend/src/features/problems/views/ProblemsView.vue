<template>
  <div style="padding:20px; height:100%; display:flex; flex-direction:column; gap:16px;">
    <div class="card-soft" style="padding:16px; display:flex; justify-content:space-between; align-items:flex-end;">
      <div>
        <h2 class="title-gradient-violet" style="margin:0 0 12px 0;">题库选题</h2>
        <div style="display:flex; gap:12px; align-items:center;">
          <el-select v-model="filter.difficulty" placeholder="难度" clearable style="width:120px" @change="handleFilter">
            <el-option label="容易" value="易" />
            <el-option label="中等" value="中" />
            <el-option label="困难" value="难" />
          </el-select>
          <el-input v-model="filter.knowledge" placeholder="搜索知识点..." clearable style="width:200px" @keyup.enter="handleFilter" />
          <el-button type="primary" class="ripple" @click="handleFilter">搜索</el-button>
          <el-button class="ripple" @click="clearFilter">清空</el-button>
          <el-tag v-if="store.total" type="success">共 {{ store.total }} 题</el-tag>
        </div>
      </div>

      <div style="display:flex; gap:12px;">
        <el-button type="success" class="ripple" @click="openDialog" :disabled="!store.selectedQuestions.length">
          创建作业 ({{ store.selectedQuestions.length }})
        </el-button>
        <el-upload 
           action="" 
           :http-request="customRequest" 
           :show-file-list="false" 
           accept=".csv,.xlsx,.xls,.json">
           <el-button class="ripple">导入题目</el-button>
        </el-upload>
      </div>
    </div>

    <el-table 
      v-loading="store.loading" 
      :data="store.questions" 
      @selection-change="handleSelection"
      border 
      style="width: 100%; flex:1;" class="card-soft">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="题干" min-width="300">
        <template #default="{ row }">
            <LatexText :content="row.question" />
        </template>
      </el-table-column>
      <el-table-column prop="difficulty_tag" label="难度" width="100" />
      <el-table-column prop="knowledge_tag" label="知识点" width="200" />
    </el-table>

    <div style="margin-top:12px; display:flex; justify-content:flex-end;">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        :total="store.total"
        @size-change="handleFilter"
        @current-change="handleFilter"
      />
    </div>

    <el-dialog v-model="dialogVisible" title="布置作业" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="作业标题">
          <el-input v-model="form.title" placeholder="如：第一章课后作业" />
        </el-form-item>
        <el-form-item label="班级 ID">
          <el-input-number v-model="form.class_id" :min="1" />
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker 
            v-model="form.deadline" 
            type="datetime" 
            placeholder="选择截止时间" 
            value-format="YYYY-MM-DDTHH:mm:ss" 
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="store.loading" @click="submitAssignment">
            确定布置
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useProblemsStore } from '../store'
import { uploadQuestions, type Question } from '../../../services/modules/problems'
import { ElMessage } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'

const store = useProblemsStore()
const dialogVisible = ref(false)

const page = ref(1)
const pageSize = ref(20)
const filter = reactive({
  difficulty: '',
  knowledge: ''
})

const form = reactive({
  title: '',
  class_id: 1,
  deadline: ''
})

onMounted(() => {
  handleFilter()
})

function handleFilter() {
  store.fetchQuestions(
    (page.value - 1) * pageSize.value, 
    pageSize.value,
    filter.difficulty || undefined,
    filter.knowledge || undefined
  )
}

function handleSelection(val: Question[]) {
  store.selectedQuestions = val
}

function clearFilter() {
  filter.difficulty = ''
  filter.knowledge = ''
  page.value = 1
  handleFilter()
}

function openDialog() {
  dialogVisible.value = true
}

async function submitAssignment() {
  if (!form.title) {
    ElMessage.warning('请输入标题')
    return
  }
  const success = await store.createAssignment({
    title: form.title,
    teacher_id: 1, // Hardcoded for now
    class_id: form.class_id,
    deadline: form.deadline || undefined,
    assigned_question_ids: store.selectedQuestions.map(q => q.id)
  })
  
  if (success) {
    ElMessage.success('作业布置成功')
    dialogVisible.value = false
    form.title = ''
    store.selectedQuestions = [] // Clear selection? Table selection clearing might need ref
  } else {
    ElMessage.error('作业布置失败')
  }
}

async function customRequest(options: any) {
  try {
    await uploadQuestions(options.file)
    ElMessage.success('上传成功')
    handleFilter()
  } catch (e) {
    ElMessage.error('上传失败')
  }
}
</script>
