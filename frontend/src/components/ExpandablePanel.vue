<template>
  <article :class="['panel-card', 'expandable-panel', panelClass, { expanded: isExpanded }]">
    <button class="ghost-btn panel-expand-btn" type="button" @click="toggleExpanded">
      {{ isExpanded ? '还原' : '放大' }}
    </button>
    <slot />
  </article>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  panelClass: {
    type: [String, Array, Object],
    default: '',
  },
})

const isExpanded = ref(false)

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}
</script>
