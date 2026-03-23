import { computed, reactive } from 'vue'

const state = reactive({
  routeLoading: false,
  requestPendingCount: 0,
})

export const pageLoadingState = reactive({
  text: '页面加载中...',
  isVisible: computed(() => state.routeLoading || state.requestPendingCount > 0),
})

export function startRouteLoading() {
  state.routeLoading = true
}

export function finishRouteLoading() {
  state.routeLoading = false
}

export async function withPageLoading(task) {
  state.requestPendingCount += 1

  try {
    return await task()
  } finally {
    if (state.requestPendingCount > 0) {
      state.requestPendingCount -= 1
    }
  }
}
