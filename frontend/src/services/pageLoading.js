import { computed, reactive } from 'vue'

const state = reactive({
  pendingCount: 0,
})

export const pageLoadingState = reactive({
  text: '页面加载中...',
  isVisible: computed(() => state.pendingCount > 0),
})

export function startRouteLoading() {
  state.pendingCount += 1
}

export function finishRouteLoading() {
  if (state.pendingCount > 0) {
    state.pendingCount -= 1
  }
}

export async function withPageLoading(task) {
  startRouteLoading()
  try {
    return await task()
  } finally {
    finishRouteLoading()
  }
}
