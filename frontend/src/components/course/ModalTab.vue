<template>
  <el-radio-group :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <el-radio-button value="text">文本</el-radio-button>
    <el-radio-button value="quiz">测验</el-radio-button>
    <el-radio-button value="ppt">PPT</el-radio-button>
    <el-radio-button value="mindmap">导图</el-radio-button>
    <el-radio-button value="interactive_html">互动教材</el-radio-button>
  </el-radio-group>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>
