import { config } from '@vue/test-utils'

// 可以在这里配置全局属性、插件等，比如 Element Plus
// 因为测试环境主要测逻辑，Element UI 的组件可以通过 stub 解决，或全局忽略未知自定义元素
config.global.stubs = {
  'el-button': true,
  'el-input': true,
  'el-form': true,
  'el-form-item': true,
  'el-icon': true,
  'el-empty': true,
  'el-dialog': true,
  'el-progress': true,
  'el-col': true,
  'el-row': true,
  'el-tag': true,
  'el-radio-group': true,
  'el-radio-button': true,
  'el-select': true,
  'el-option': true,
  'el-tabs': true,
  'el-tab-pane': true,
  'el-table': true,
  'el-table-column': true,
  'el-pagination': true,
  'el-skeleton': true,
  'el-skeleton-item': true,
  'el-image': true,
  'el-alert': true,
}
