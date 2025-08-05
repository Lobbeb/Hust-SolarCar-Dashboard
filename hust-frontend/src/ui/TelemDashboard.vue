<template>
  <div class="shell">
    <!-- ===== header ===== -->
    <header>
      <div class="header-left">
        <h1>HUST Solar Car Dashboard</h1>
        <!-- Connection status indicator -->
        <div class="connection-info">
          <span :class="['status-dot', connectionClass]"></span>
          <span class="status-text">{{ connectionText }}</span>
          <small v-if="store.lastFetch" class="last-update">
            Last: {{ lastUpdateTime }}
          </small>
        </div>
      </div>
      
      <div class="header-controls">
        <!-- Global error display -->
        <div v-if="store.error" class="global-error">
          <span>⚠️ {{ store.error }}</span>
          <button @click="store.retry()" class="retry-btn-small">Retry</button>
        </div>
        
        <!-- Paus / Start -->
        <button class="pause" @click="toggleLive" :disabled="store.loading">
          {{ store.live ? "⏸ Pause" : "▶ Start" }}
        </button>

        <!-- Time Window -->
        <select v-model="limit" class="range" @change="onLimitChange">
          <option :value="20">20 points</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
        
        <!-- Manual refresh -->
        <button @click="refresh" :disabled="store.loading" class="refresh-btn">
          🔄 Refresh
        </button>
      </div>
    </header>

    <!-- Global loading overlay -->
    <div v-if="store.loading && !store.hasData" class="global-loading">
      <div class="spinner-large"></div>
      <p>Loading telemetry data...</p>
    </div>

    <!-- ========= Content ========= -->
    <main class="grid">
      <MetricPanel title="Battery" :metrics="battery" />
      <MetricPanel title="Motor" :metrics="motor" />
      <MetricPanel title="MPPT" :metrics="mppt" />
      <MetricPanel title="Vehicle" :metrics="vehicle" />
    </main>
  </div>
</template>

<script setup>
import { ref, provide, computed, watch } from "vue";
import { useTelemStore } from "../store.js";
import MetricPanel from "./MetricPanel.vue";

// Store access
const store = useTelemStore();

/* live flag + time window shared via provide */
const liveFlag = ref(true);
const limit = ref(20);
provide("liveFlag", liveFlag);
provide("limit", limit);

// Computed properties for UI state
const connectionClass = computed(() => {
  switch (store.connectionStatus) {
    case 'connected': return 'online';
    case 'disconnected': return 'offline';
    case 'error': return 'error';
    default: return 'offline';
  }
});

const connectionText = computed(() => {
  switch (store.connectionStatus) {
    case 'connected': return 'Live';
    case 'disconnected': return 'Disconnected';
    case 'error': return 'Error';
    default: return 'Connecting...';
  }
});

const lastUpdateTime = computed(() => {
  if (!store.lastFetch) return '';
  return new Date(store.lastFetch).toLocaleTimeString();
});

// Watch for live flag changes and sync with store
watch(liveFlag, (newValue) => {
  if (newValue !== store.live) {
    store.toggleLive();
  }
});

// Watch store live state and sync with local flag
watch(() => store.live, (newValue) => {
  if (newValue !== liveFlag.value) {
    liveFlag.value = newValue;
  }
});

// Functions
function toggleLive() {
  liveFlag.value = !liveFlag.value;
  store.toggleLive();
}

function onLimitChange() {
  // Only refresh if not in live mode or if data is stale
  if (!store.live || store.isStale) {
    store.refresh(limit.value);
  }
}

function refresh() {
  store.refresh(limit.value);
}

/* metric lists */
const battery = [
  { label: "Voltage (V)", key: "battery_volt" },
  { label: "Current (A)", key: "battery_current" },
  { label: "Avg Temp (°C)", key: "battery_cell_average_temp" },
];
const motor = [
  { label: "Motor Temp (°C)", key: "motor_temp" },
  { label: "Motor Current", key: "motor_current" },
  { label: "Controller Temp", key: "motor_controller_temp" },
];
const mppt = [
  { label: "Total Watt (W)", key: "MPPT_total_watt" },
  { label: "MPPT1 Watt", key: "MPPT1_watt" },
  { label: "MPPT2 Watt", key: "MPPT2_watt" },
  { label: "MPPT3 Watt", key: "MPPT3_watt" },
];
const vehicle = [
  { label: "Speed (km/h)", key: "velocity" },
  { label: "Distance (m)", key: "distance_travelled" },
];
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ---------- header ---------- */
header {
  background: #0009;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 12px 24px;
  box-shadow: 0 2px 6px #0007;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

h1 {
  margin: 0;
  font-size: 1.25rem;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.online {
  background: #00ff88;
  box-shadow: 0 0 6px #00ff88;
}

.status-dot.offline {
  background: #ff4444;
  box-shadow: 0 0 6px #ff4444;
}

.status-dot.error {
  background: #ff8800;
  box-shadow: 0 0 6px #ff8800;
}

.status-text {
  color: #fff;
  font-weight: 500;
}

.last-update {
  color: #bbb;
  margin-left: 0.5rem;
}

.global-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 68, 68, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  color: #ff4444;
  font-size: 0.85rem;
}

.retry-btn-small {
  background: #ff4444;
  color: white;
  border: none;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.75rem;
  cursor: pointer;
}

.pause {
  background: var(--brand-soft);
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: background 0.2s;
}

.pause:hover:not(:disabled) {
  background: var(--brand);
}

.pause:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn {
  background: #333;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #555;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.range {
  background: #2b2b2b;
  color: #fff;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Global loading overlay */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: white;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 6px solid #444;
  border-top: 6px solid var(--brand, #00ff88);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ---------- grid ---------- */
main.grid {
  flex: 1;
  display: grid;
  gap: 20px;
  padding: 20px;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
}

@media (max-width: 768px) {
  main.grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .header-left, .header-controls {
    gap: 0.5rem;
  }
  
  h1 {
    font-size: 1.1rem;
  }
  
  .connection-info {
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  main.grid {
    grid-template-columns: 1fr;
  }
  
  header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .header-left, .header-controls {
    justify-content: center;
  }
}
</style>
