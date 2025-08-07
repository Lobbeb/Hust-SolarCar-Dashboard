<template>
  <div class="cleanup-panel">
    <h3>🧹 Database Cleanup Management</h3>
    
    <!-- Status Overview -->
    <div class="cleanup-status" v-if="stats">
      <div class="status-grid">
        <div class="status-card">
          <div class="status-number">{{ formatNumber(stats.total_records) }}</div>
          <div class="status-label">Total Records</div>
        </div>
        <div class="status-card" :class="{ 'warning': stats.total_deletable > 10000, 'critical': stats.total_deletable > 50000 }">
          <div class="status-number">{{ formatNumber(stats.total_deletable) }}</div>
          <div class="status-label">Deletable Records</div>
        </div>
        <div class="status-card">
          <div class="status-number">{{ Math.round(deletionPercentage) }}%</div>
          <div class="status-label">Can Be Cleaned</div>
        </div>
      </div>
    </div>

    <!-- Recommendations -->
    <div class="recommendations" v-if="recommendations">
      <div class="recommendation-card" :class="recommendations.recommended_action">
        <h4>📊 Cleanup Recommendation</h4>
        <p class="recommendation-text">{{ getRecommendationText() }}</p>
        
        <div class="recommendation-actions">
          <button 
            @click="runDryRun" 
            :disabled="loading"
            class="btn btn-info"
          >
            🔍 Preview Cleanup
          </button>
          
          <button 
            v-if="recommendations.recommended_action !== 'no_action'"
            @click="showExecuteDialog = true" 
            :disabled="loading"
            class="btn btn-warning"
          >
            🗑️ Execute Cleanup
          </button>
        </div>
      </div>
    </div>

    <!-- Table Details -->
    <div class="table-details" v-if="stats">
      <h4>📋 Table Statistics</h4>
      <div class="table-grid">
        <div 
          v-for="(tableStats, tableName) in stats.table_stats" 
          :key="tableName" 
          class="table-card"
        >
          <h5>{{ getTableDisplayName(tableName) }}</h5>
          <div class="table-stats">
            <div class="stat">
              <span class="stat-label">Records:</span>
              <span class="stat-value">{{ formatNumber(tableStats.total_records) }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Deletable:</span>
              <span class="stat-value warning">{{ formatNumber(tableStats.records_to_delete) }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Retention:</span>
              <span class="stat-value">{{ tableStats.retention_days }} days</span>
            </div>
            <div class="stat protection-info">
              <span class="stat-label">🛡️ Protected:</span>
              <span class="stat-value">Latest {{ getLatestProtected(tableName) }} records</span>
            </div>
            <div class="stat" v-if="tableStats.oldest_record">
              <span class="stat-label">Oldest:</span>
              <span class="stat-value">{{ formatDate(tableStats.oldest_record) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <button @click="refreshStats" :disabled="loading" class="btn btn-primary">
        🔄 Refresh Stats
      </button>
      
      <button @click="toggleScheduler" :disabled="loading" class="btn btn-secondary">
        {{ schedulerEnabled ? '⏸️ Stop Auto-Cleanup' : '▶️ Start Auto-Cleanup' }}
      </button>
    </div>

    <!-- Execute Confirmation Dialog -->
    <div v-if="showExecuteDialog" class="modal-overlay" @click="showExecuteDialog = false">
      <div class="modal-dialog" @click.stop>
        <h3>⚠️ Confirm Database Cleanup</h3>
        <p>This will permanently delete <strong>{{ formatNumber(stats?.total_deletable || 0) }}</strong> old records.</p>
        <p class="warning-text">This action cannot be undone!</p>
        
        <div class="confirmation-input">
          <label>
            <input 
              type="checkbox" 
              v-model="confirmCleanup"
            >
            I understand this will permanently delete data
          </label>
        </div>
        
        <div class="modal-actions">
          <button @click="showExecuteDialog = false" class="btn btn-secondary">
            Cancel
          </button>
          <button 
            @click="executeCleanup" 
            :disabled="!confirmCleanup || loading"
            class="btn btn-danger"
          >
            🗑️ Execute Cleanup
          </button>
        </div>
      </div>
    </div>

    <!-- Results Display -->
    <div v-if="lastResult" class="results-display">
      <h4>{{ lastResult.dry_run ? '🔍 Cleanup Preview Results' : '✅ Cleanup Results' }}</h4>
      <div class="result-summary">
        <p>
          <strong>{{ lastResult.dry_run ? 'Would delete' : 'Deleted' }}:</strong>
          {{ formatNumber(lastResult.total_deleted) }} records
        </p>
        <p v-if="!lastResult.dry_run">
          <strong>Duration:</strong> {{ lastResult.duration?.toFixed(2) }} seconds
        </p>
      </div>
      
      <div class="result-details">
        <div 
          v-for="(tableResult, tableName) in lastResult.tables_processed" 
          :key="tableName"
          class="result-item"
        >
          <span class="table-name">{{ getTableDisplayName(tableName) }}:</span>
          <span class="delete-count">{{ formatNumber(tableResult.records_deleted) }} records</span>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'CleanupPanel',
  setup() {
    const stats = ref(null)
    const recommendations = ref(null)
    const lastResult = ref(null)
    const loading = ref(false)
    const loadingMessage = ref('')
    const showExecuteDialog = ref(false)
    const confirmCleanup = ref(false)
    const schedulerEnabled = ref(true)

    const deletionPercentage = computed(() => {
      if (!stats.value) return 0
      return (stats.value.total_deletable / stats.value.total_records) * 100
    })

    const formatNumber = (num) => {
      return new Intl.NumberFormat().format(num)
    }

    const formatDate = (dateStr) => {
      return new Date(dateStr).toLocaleDateString()
    }

    const getLatestProtected = (tableName) => {
      const protectionCounts = {
        'Battery Data Table': 500,
        'Motor Data Table': 500,
        'MPPT Data Table': 500,
        'Vehicle Data Table': 300
      }
      return protectionCounts[tableName] || 300
    }

    const getTableDisplayName = (tableName) => {
      const names = {
        'Battery Data Table': 'Battery',
        'Motor Data Table': 'Motor',
        'MPPT Data Table': 'Solar (MPPT)',
        'Vehicle Data Table': 'Vehicle'
      }
      return names[tableName] || tableName
    }

    const getRecommendationText = () => {
      if (!recommendations.value) return ''
      
      const action = recommendations.value.recommended_action
      const totalRecords = recommendations.value.total_records
      const deletableRecords = recommendations.value.total_deletable
      
      switch (action) {
        case 'cleanup_urgent':
          return `🚨 Urgent cleanup needed! Database has ${formatNumber(totalRecords)} records with ${formatNumber(deletableRecords)} deletable. Performance may be affected.`
        case 'cleanup_recommended':
          return `⚠️ Cleanup recommended. ${formatNumber(deletableRecords)} old records can be safely removed to improve performance.`
        case 'cleanup_beneficial':
          return `💡 Cleanup would be beneficial. ${formatNumber(deletableRecords)} records can be removed to free up space.`
        default:
          return `✅ Database is healthy. Only ${formatNumber(deletableRecords)} old records available for cleanup.`
      }
    }

    const refreshStats = async () => {
      loading.value = true
      loadingMessage.value = 'Loading database statistics...'
      
      try {
        const [statsResponse, recsResponse] = await Promise.all([
          axios.get('/admin/cleanup/stats'),
          axios.get('/admin/cleanup/recommendations')
        ])
        
        stats.value = statsResponse.data
        recommendations.value = recsResponse.data.recommendations
      } catch (error) {
        console.error('Failed to refresh stats:', error)
        alert('Failed to load cleanup statistics')
      } finally {
        loading.value = false
      }
    }

    const runDryRun = async () => {
      loading.value = true
      loadingMessage.value = 'Running cleanup preview...'
      
      try {
        const response = await axios.post('/admin/cleanup/dry-run')
        lastResult.value = response.data.result
        
        // Refresh stats after dry run
        await refreshStats()
      } catch (error) {
        console.error('Dry run failed:', error)
        alert('Cleanup preview failed')
      } finally {
        loading.value = false
      }
    }

    const executeCleanup = async () => {
      loading.value = true
      loadingMessage.value = 'Executing database cleanup...'
      showExecuteDialog.value = false
      confirmCleanup.value = false
      
      try {
        const response = await axios.post('/admin/cleanup/execute', {
          confirm: true
        })
        
        lastResult.value = response.data.result
        
        // Refresh stats after cleanup
        await refreshStats()
        
        alert(`Cleanup completed! Deleted ${formatNumber(lastResult.value.total_deleted)} records.`)
      } catch (error) {
        console.error('Cleanup execution failed:', error)
        alert('Cleanup execution failed')
      } finally {
        loading.value = false
      }
    }

    const toggleScheduler = async () => {
      loading.value = true
      loadingMessage.value = schedulerEnabled.value ? 'Stopping scheduler...' : 'Starting scheduler...'
      
      try {
        const endpoint = schedulerEnabled.value 
          ? '/admin/cleanup/scheduler/stop'
          : '/admin/cleanup/scheduler/start'
        
        await axios.post(endpoint)
        schedulerEnabled.value = !schedulerEnabled.value
        
      } catch (error) {
        console.error('Failed to toggle scheduler:', error)
        alert('Failed to toggle cleanup scheduler')
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      refreshStats()
    })

    return {
      stats,
      recommendations,
      lastResult,
      loading,
      loadingMessage,
      showExecuteDialog,
      confirmCleanup,
      schedulerEnabled,
      deletionPercentage,
      formatNumber,
      formatDate,
      getLatestProtected,
      getTableDisplayName,
      getRecommendationText,
      refreshStats,
      runDryRun,
      executeCleanup,
      toggleScheduler
    }
  }
}
</script>

<style scoped>
.cleanup-panel {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}

.cleanup-status {
  margin-bottom: 1.5rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.status-card {
  background: var(--surface-color, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.status-card.warning {
  border-color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
}

.status-card.critical {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
}

.status-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color, #00bcd4);
}

.status-label {
  font-size: 0.9rem;
  color: var(--text-secondary, #aaa);
  margin-top: 0.25rem;
}

.recommendations {
  margin-bottom: 1.5rem;
}

.recommendation-card {
  background: var(--surface-color, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1rem;
}

.recommendation-card.cleanup_urgent {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
}

.recommendation-card.cleanup_recommended {
  border-color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
}

.recommendation-card.cleanup_beneficial {
  border-color: #2196f3;
  background: rgba(33, 150, 243, 0.1);
}

.recommendation-text {
  margin: 0.5rem 0 1rem 0;
  line-height: 1.4;
}

.recommendation-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.table-details {
  margin-bottom: 1.5rem;
}

.table-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.table-card {
  background: var(--surface-color, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1rem;
}

.table-card h5 {
  margin: 0 0 0.75rem 0;
  color: var(--primary-color, #00bcd4);
}

.table-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: var(--text-secondary, #aaa);
  font-size: 0.9rem;
}

.stat-value {
  font-weight: bold;
}

.stat-value.warning {
  color: #ff9800;
}

.protection-info .stat-value {
  color: #00ff88;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color, #00bcd4);
  color: white;
}

.btn-secondary {
  background: var(--secondary-color, #666);
  color: white;
}

.btn-info {
  background: #2196f3;
  color: white;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: var(--surface-color, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1.5rem;
  max-width: 500px;
  width: 90%;
}

.modal-dialog h3 {
  margin: 0 0 1rem 0;
  color: #f44336;
}

.warning-text {
  color: #ff9800;
  font-weight: bold;
  margin: 0.5rem 0 1rem 0;
}

.confirmation-input {
  margin: 1rem 0;
}

.confirmation-input label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.results-display {
  background: var(--surface-color, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.results-display h4 {
  margin: 0 0 1rem 0;
  color: var(--primary-color, #00bcd4);
}

.result-summary {
  margin-bottom: 1rem;
}

.result-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--border-color, #444);
}

.table-name {
  color: var(--text-secondary, #aaa);
}

.delete-count {
  font-weight: bold;
  color: #ff9800;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #444);
  border-top: 4px solid var(--primary-color, #00bcd4);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
