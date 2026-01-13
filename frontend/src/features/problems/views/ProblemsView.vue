<template>
  <div style="padding:20px; height:100%; display:flex; flex-direction:column; gap:16px;">
    <div class="card-soft" style="padding:16px; display:flex; justify-content:space-between; align-items:flex-end;">
      <div>
        <h2 class="title-gradient-violet" style="margin:0 0 12px 0;">Problem Selection</h2>
        <div style="display:flex; gap:12px; align-items:center;">
          <el-select v-model="filter.difficulty" placeholder="Difficulty" clearable style="width:120px" @change="handleFilter">
            <el-option label="Easy" value="易" />
            <el-option label="Medium" value="中" />
            <el-option label="Hard" value="难" />
          </el-select>
          <el-input v-model="filter.knowledge" placeholder="Search knowledge..." clearable style="width:200px" @keyup.enter="handleFilter" />
          <el-button type="primary" class="ripple" @click="handleFilter">Search</el-button>
          <el-button class="ripple" @click="clearFilter">Clear</el-button>
          <el-tag v-if="store.total" type="success">{{ store.total }} items</el-tag>
        </div>
      </div>

      <div style="display:flex; gap:12px;">
        <el-button type="success" class="ripple" @click="openDialog" :disabled="!store.selectedQuestions.length">
          Create Assignment ({{ store.selectedQuestions.length }})
        </el-button>
        <el-upload 
           action="" 
           :http-request="customRequest" 
           :show-file-list="false" 
           accept=".docx,.pdf,.png,.jpg,.jpeg">
           <el-button class="ripple">Import Questions</el-button>
        </el-upload>
        <el-button class="btn-outline" @click="openAssignUpload">Upload Document to Create Assignment</el-button>
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
      <el-table-column label="Stem" min-width="300">
        <template #default="{ row }">
            <LatexText :content="row.question" />
        </template>
      </el-table-column>
      <el-table-column prop="difficulty_tag" label="Difficulty" width="100" />
      <el-table-column prop="knowledge_tag" label="Knowledge" width="200" />
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

    <el-dialog v-model="dialogVisible" title="Assign Homework" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="Title">
          <el-input v-model="form.title" placeholder="e.g., Chapter 1 Homework" />
        </el-form-item>
        <el-form-item label="Class">
          <el-select v-model="form.class_id" placeholder="Select Class" style="width:100%">
            <el-option v-for="c in myClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Deadline">
          <el-date-picker 
            v-model="form.deadline" 
            type="datetime" 
            placeholder="Pick a deadline" 
            value-format="YYYY-MM-DDTHH:mm:ss" 
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" :loading="store.loading" @click="submitAssignment">
            Confirm
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <el-dialog v-model="uploadDialog" title="Upload Document and Create Assignment" width="520px">
      <el-form label-width="110px">
        <el-form-item label="File">
          <el-upload
            action=""
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleUploadFileChange"
            accept=".png,.jpg,.jpeg,.pdf,.docx"
          >
            <el-button type="primary">Choose File</el-button>
          </el-upload>
          <div style="margin-left:12px; color:#6b7280;">Automatically parse questions and deduplicate to generate assignment</div>
        </el-form-item>
        <el-form-item label="Title">
          <el-input v-model="uploadForm.title" placeholder="e.g., Chapter 1 Homework" />
        </el-form-item>
        <el-form-item label="Class">
          <el-select v-model="uploadForm.class_id" placeholder="Select Class" style="width:100%">
            <el-option v-for="c in myClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Deadline">
          <el-date-picker v-model="uploadForm.deadline" type="datetime" placeholder="Pick a time" />
        </el-form-item>
        <div v-if="creating" style="margin-top:8px;">
          <div style="margin-bottom:6px; color:#374151; font-weight:500;">{{ progressText }}</div>
          <el-progress :percentage="progress" :status="progressStatus" :text-inside="true" :stroke-width="18" />
        </div>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog=false" :disabled="creating">Close</el-button>
        <el-button type="primary" @click="doCreateAssignment" :loading="creating">Create Assignment</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useProblemsStore } from '../store'
import { uploadQuestions, type Question } from '../../../services/modules/problems'
import { ElMessage } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'
import { api } from '../../../services/apiClient'
import { listTeacherClasses } from '../../../services/modules/classes'
import { useAuthStore } from '../../../stores/auth'
import dayjs from 'dayjs'

const store = useProblemsStore()
const dialogVisible = ref(false)
const uploadDialog = ref(false)
const selectedFile = ref<File | null>(null)
const router = useRouter()
const auth = useAuthStore()

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
const uploadForm = reactive({
  title: '',
  class_id: 1,
  deadline: ''
})
const myClasses = ref<Array<{id:number; name:string}>>([])
const creating = ref(false)
const progress = ref(0)
const progressStatus = ref<'success'|'exception'|'active'>('active')
const progressText = ref('Preparing upload...')

onMounted(async () => {
  handleFilter()
  try {
    myClasses.value = await listTeacherClasses()
    const first = myClasses.value.length ? myClasses.value[0] : undefined
    if (first) {
      form.class_id = first.id
      uploadForm.class_id = first.id
    } 
  } catch {}
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
function openAssignUpload() {
  uploadDialog.value = true
}

async function submitAssignment() {
  if (!form.title) {
    ElMessage.warning('Please enter a title')
    return
  }
  const success = await store.createAssignment({
    title: form.title,
    teacher_id: auth.user?.teacher_id || 0,
    class_id: form.class_id,
    deadline: form.deadline || undefined,
    assigned_question_ids: store.selectedQuestions.map(q => q.id)
  })
  
  if (success) {
    ElMessage.success('Assignment created successfully')
    dialogVisible.value = false
    form.title = ''
    store.selectedQuestions = [] // Clear selection? Table selection clearing might need ref
  } else {
    ElMessage.error('Failed to create assignment')
  }
}

async function customRequest(options: any) {
  try {
    store.loading = true
    const res = await uploadQuestions(options.file)
    const data = res?.data || {}
    if (data.status === 'success') {
      const created = Number(data.created || 0)
      const duplicates = Number(data.duplicates || 0)
      const total = Number(data.total || created + duplicates)
      ElMessage.success(`Import complete: ${created} new, ${duplicates} duplicates (total ${total}).`)
    } else {
      const msg = String(data.error || 'Import failed')
      ElMessage.error(`Import failed: ${msg}`)
    }
    handleFilter()
  } catch (e) {
    try {
      // Attempt to extract axios error shape
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err: any = e
      const msg = (err?.response?.data?.error || err?.message) ? String(err?.response?.data?.error || err?.message) : 'Import failed'
      ElMessage.error(msg)
    } catch {
      ElMessage.error('Import failed')
    }
  } finally {
    store.loading = false
  }
}


function handleUploadFileChange(file: any) {
  selectedFile.value = (file && file.raw) ? file.raw as File : null
}
async function doCreateAssignment() {
  if (!selectedFile.value) {
    ElMessage.warning('Please select a file first')
    return
  }
  try {
    creating.value = true
    progress.value = 5
    progressStatus.value = 'active'
    progressText.value = 'Uploading file...'
    const timer = setInterval(() => {
      // Simulate staged progress: up to 90%, wait for server
      if (progress.value < 90) {
        // Faster early, slower later
        progress.value += progress.value < 50 ? 5 : 2
      }
    }, 400)

    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('class_id', String(uploadForm.class_id))
    if (uploadForm.title) formData.append('title', uploadForm.title)
    if (uploadForm.deadline) formData.append('deadline', dayjs(uploadForm.deadline).format('YYYY-MM-DDTHH:mm:ss'))
    progressText.value = 'Parsing document and checking duplicates...'
    const r = await api.post('/api/assignments/upload', formData, { timeout: 60000 })
    progress.value = 100
    progressStatus.value = 'success'
    progressText.value = 'Created'
    ElMessage.success(`Assignment created, ID: ${r.data.id}`)
    uploadDialog.value = false
    selectedFile.value = null
    clearInterval(timer)
    creating.value = false
    // Redirect to student assignments page
    if (r?.data?.id) {
      router.push(`/paper/${r.data.id}`)
    }
  } catch (e: any) {
    console.error(e)
    const msg = (e?.response?.data?.detail) ? String(e.response.data.detail) : 'Failed to create assignment'
    progressStatus.value = 'exception'
    progressText.value = msg
    ElMessage.error(msg)
    creating.value = false
  }
}
</script>
