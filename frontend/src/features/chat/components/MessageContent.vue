<template>
  <div class="md-content" ref="contentRef" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
// @ts-ignore
import renderMathInElement from 'katex/dist/contrib/auto-render.mjs'

const props = defineProps<{
  content: string
}>()

const contentRef = ref<HTMLElement | null>(null)

marked.setOptions({ gfm: true, breaks: true })

const renderedContent = computed(() => {
  return render(props.content)
})

watch(renderedContent, async () => {
    await nextTick()
    renderMath()
})

onMounted(() => {
    renderMath()
})

function renderMath() {
    if (contentRef.value) {
        try {
             renderMathInElement(contentRef.value, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '\\[', right: '\\]', display: true },
                    { left: '\\(', right: '\\)', display: false },
                    { left: '$', right: '$', display: false }
                ],
                throwOnError: false
            })
        } catch (e) {
            console.error("Math render error", e)
        }
    }
}

function render(t: string) {
  let s = (t || '')
    // 将单反斜杠行尾换行转为 LaTeX 的 \\ 换行
    .replace(/(?<!\\)\\\s*$/gm, '\\\\')
    // 统一一些常见错误空格：\sin alpha -> \sin\alpha
    .replace(/\\(sin|cos|tan|cot|sec|csc)\s+([a-zA-Z]+)/g, '\\$1\\$2')
    // \vec a -> \vec{a}
    .replace(/\\vec\s+([a-zA-Z])/g, '\\vec{$1}')
    // 将 $$ 换行块（$$<CRLF>...<CRLF>$$）统一为 \\[ ... \\]
    .replace(/(^|\r?\n)\s*\$\$\s*(?:\r?\n)([\s\S]*?)(?:\r?\n)\s*\$\$(?=\r?\n|$)/g, '$1\\\\[$2\\\\]')
    // 将 [ ... ] 包裹的 LaTeX 块转为 \[ ... \]（仅当包含对齐/分段环境）
    .replace(/\[\s*([\s\S]*?\\begin\{(?:aligned|cases)\}[\s\S]*?\\end\{(?:aligned|cases)\}[\s\S]*?)\s*\]/g, '\\[$1\\]')
    // 去除无意义的 \x、\y（常见误写）
    .replace(/\\([xy])\b/g, '$1')

  // 保护 LaTeX 公式不被 marked 解析（占位使用安全的自定义标签，避免被 Markdown 语法改写）
  const mathBlocks: string[] = []
  const protect = (regex: RegExp) => {
    s = s.replace(regex, (match) => {
      mathBlocks.push(match)
      const i = mathBlocks.length - 1
      return `<math-block data-i="${i}"></math-block>`
    })
  }

  // 注意顺序：先长后短，先块后行
  protect(/\\\[([\s\S]*?)\\\]/g)
  protect(/\$\$([\s\S]*?)\$\$/g)
  protect(/\\\(([\s\S]*?)\\\)/g)
  protect(/\$([^\n$]+)\$/g)

  const html = marked.parse(s) as string
  
  // 还原 LaTeX 公式
  const restoredHtml = html.replace(/<math-block[^>]*data-i="(\d+)"[^>]*><\/math-block>/g, (_m, index) => {
    const i = parseInt(index)
    return mathBlocks[i] || ''
  })

  return DOMPurify.sanitize(restoredHtml)
}
</script>

<style scoped>
.md-content :deep(code) { background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }
.md-content :deep(pre code) { display: block; padding: 12px; overflow: auto; }
</style>