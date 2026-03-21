<template>
  <article :class="['panel-card', 'expandable-panel', panelClass, { expanded: isExpanded }]">
    <button
      :aria-label="buttonLabel"
      :title="buttonLabel"
      class="ghost-btn panel-expand-btn"
      type="button"
      @click="toggleExpanded"
    >
      <img :alt="buttonLabel" :src="isExpanded ? collapseIcon : expandIcon" class="panel-expand-icon" />
    </button>
    <slot />
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'

import collapseIcon from '../assets/img/缩小.png'
import expandIcon from '../assets/img/展开.png'

defineProps({
  panelClass: {
    type: [String, Array, Object],
    default: '',
  },
})

const isExpanded = ref(false)
const buttonLabel = computed(() => (isExpanded.value ? '还原列表区域' : '展开列表区域'))

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}
</script>
