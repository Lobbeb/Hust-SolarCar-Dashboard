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
        <!-- CRITICAL ALERTS BAR -->
        <div v-if="criticalAlerts.length > 0" class="critical-alerts-bar">
          <div v-for="alert in criticalAlerts" :key="alert.id" 
               :class="['critical-alert', alert.severity]">
            <span class="alert-icon">{{ alert.icon }}</span>
            <span class="alert-text">{{ alert.message }}</span>
            <button @click="dismissAlert(alert.id)" class="dismiss-btn">✕</button>
          </div>
        </div>

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
    <!-- Energy Overview Bar -->
    <div class="energy-overview">
      <div class="energy-card">
        <div class="energy-label">Solar Input</div>
        <div class="energy-value solar">{{ solarPower }}W</div>
        <div class="energy-sub">{{ solarPower > 800 ? 'Excellent' : solarPower > 500 ? 'Good' : solarPower > 200 ? 'Poor' : 'Critical' }}</div>
      </div>
      <div class="energy-card">
        <div class="energy-label">Power Draw</div>
        <div class="energy-value battery">{{ batteryPower }}W</div>
        <div class="energy-sub">{{ batteryPower < 1000 ? 'Efficient' : batteryPower < 2000 ? 'Moderate' : 'High' }}</div>
      </div>
      <div class="energy-card">
        <div class="energy-label">Net Balance</div>
        <div :class="['energy-value', energyBalanceClass]">{{ energyBalance }}W</div>
        <div class="energy-sub">{{ energyBalance > 0 ? 'Surplus' : 'Deficit' }}</div>
      </div>
      <div class="energy-card">
        <div class="energy-label">Race Strategy</div>
        <div :class="['energy-value', raceStrategy.isSustainable ? 'positive' : 'critical']">
          {{ raceStrategy.isSustainable ? 'SUSTAIN' : 'ADJUST' }}
        </div>
        <div class="energy-sub">{{ raceStrategy.efficiency }} km/h/W</div>
      </div>
      <div class="energy-card strategy-card">
        <div class="energy-label">Recommendation</div>
        <div class="strategy-text">{{ raceStrategy.recommendation }}</div>
      </div>
    </div>

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

// Critical Alert System
const dismissedAlerts = ref(new Set());

const criticalAlerts = computed(() => {
  const alerts = [];
  
  // Check battery data for alerts - BWSC optimized thresholds
  if (store.raw.battery_data?.length > 0) {
    const latest = store.raw.battery_data[0];
    
    // BWSC Battery voltage management (48V system)
    if (latest.battery_volt < 48) {
      alerts.push({
        id: 'critical-battery-volt',
        severity: 'critical',
        icon: '🔋',
        message: `EMERGENCY: Battery ${latest.battery_volt}V - Find charging immediately!`
      });
    } else if (latest.battery_volt < 52) {
      alerts.push({
        id: 'low-battery-volt',
        severity: 'warning',
        icon: '⚠️',
        message: `Low battery: ${latest.battery_volt}V - Plan charging stop soon`
      });
    }
    
    // Australian outback temperature limits
    if (latest.battery_cell_high_temp > 55) {
      alerts.push({
        id: 'battery-overheat',
        severity: 'critical',
        icon: '🌡️',
        message: `Battery overheating: ${latest.battery_cell_high_temp}°C - Find shade NOW!`
      });
    } else if (latest.battery_cell_high_temp > 45) {
      alerts.push({
        id: 'battery-warm',
        severity: 'warning',
        icon: '🌡️',
        message: `Battery warming: ${latest.battery_cell_high_temp}°C - Monitor closely`
      });
    }
    
    // Power consumption for multi-day race
    if (Math.abs(latest.battery_current) > 50) {
      alerts.push({
        id: 'critical-current',
        severity: 'critical',
        icon: '⚡',
        message: `CRITICAL power draw: ${Math.abs(latest.battery_current)}A - Unsustainable!`
      });
    } else if (Math.abs(latest.battery_current) > 35) {
      alerts.push({
        id: 'high-current',
        severity: 'warning',
        icon: '⚡',
        message: `High power consumption: ${Math.abs(latest.battery_current)}A`
      });
    }
  }
  
  // Check motor data for outback racing conditions
  if (store.raw.motor_data?.length > 0) {
    const latest = store.raw.motor_data[0];
    
    // Motor protection in Australian heat
    if (latest.motor_temp > 85) {
      alerts.push({
        id: 'motor-critical',
        severity: 'critical',
        icon: '🔥',
        message: `MOTOR CRITICAL: ${latest.motor_temp}°C - STOP IMMEDIATELY!`
      });
    } else if (latest.motor_temp > 70) {
      alerts.push({
        id: 'motor-overheat',
        severity: 'warning',
        icon: '🌡️',
        message: `Motor hot: ${latest.motor_temp}°C - Reduce power/speed`
      });
    }
    
    // Controller thermal management
    if (latest.motor_controller_temp > 75) {
      alerts.push({
        id: 'controller-critical',
        severity: 'critical',
        icon: '🔥',
        message: `Controller overheating: ${latest.motor_controller_temp}°C - DANGER!`
      });
    } else if (latest.motor_controller_temp > 65) {
      alerts.push({
        id: 'controller-warm',
        severity: 'warning',
        icon: '🌡️',
        message: `Controller warming: ${latest.motor_controller_temp}°C`
      });
    }
  }
  
  // Australian road speed limits for BWSC
  if (store.raw.vehicle_data?.length > 0) {
    const latest = store.raw.vehicle_data[0];
    
    if (latest.velocity > 135) {
      alerts.push({
        id: 'speed-critical',
        severity: 'critical',
        icon: '🚨',
        message: `SPEED VIOLATION: ${latest.velocity} km/h - Over NT highway limit!`
      });
    } else if (latest.velocity > 105) {
      alerts.push({
        id: 'speed-warning',
        severity: 'warning',
        icon: '🚗',
        message: `Approaching speed limit: ${latest.velocity} km/h`
      });
    }
  }
  
  // Solar efficiency alerts for race strategy
  if (store.raw.mppt_data?.length > 0) {
    const latest = store.raw.mppt_data[0];
    
    if (latest.MPPT_total_watt < 200) {
      alerts.push({
        id: 'solar-critical',
        severity: 'critical',
        icon: '☁️',
        message: `Very low solar: ${latest.MPPT_total_watt}W - Heavy clouds/shade`
      });
    } else if (latest.MPPT_total_watt < 500) {
      alerts.push({
        id: 'solar-low',
        severity: 'warning',
        icon: '🌤️',
        message: `Low solar efficiency: ${latest.MPPT_total_watt}W - Check angle`
      });
    }
  }
  
  // Filter out dismissed alerts
  return alerts.filter(alert => !dismissedAlerts.value.has(alert.id));
});

// Energy Management Calculations - BWSC Race Optimized
const solarPower = computed(() => {
  if (store.raw.mppt_data?.length > 0) {
    const latest = store.raw.mppt_data[0];
    return Math.round(latest.MPPT_total_watt || 0);
  }
  return 0;
});

const batteryPower = computed(() => {
  if (store.raw.battery_data?.length > 0) {
    const latest = store.raw.battery_data[0];
    // Use actual power calculation: P = V × I
    const power = Math.abs((latest.battery_volt || 0) * (latest.battery_current || 0));
    return Math.round(power);
  }
  return 0;
});

const energyBalance = computed(() => {
  const balance = solarPower.value - batteryPower.value;
  return Math.round(balance);
});

const energyBalanceClass = computed(() => {
  if (energyBalance.value > 200) return 'positive';      // Good surplus
  if (energyBalance.value > 0) return 'slight-positive'; // Small surplus
  if (energyBalance.value > -500) return 'negative';     // Manageable deficit
  return 'critical';                                     // Unsustainable deficit
});

const efficiency = computed(() => {
  if (batteryPower.value === 0) return 0;
  if (solarPower.value === 0) return 0;
  
  // Solar efficiency: how much solar power vs consumption
  const eff = (solarPower.value / batteryPower.value) * 100;
  return Math.round(Math.min(eff, 999)); // Cap at 999%
});

// BWSC Race Strategy Calculations
const raceStrategy = computed(() => {
  const currentSpeed = store.raw.vehicle_data?.[0]?.velocity || 0;
  const currentPower = batteryPower.value;
  const currentSolar = solarPower.value;
  
  return {
    // Energy sustainability indicator
    isSustainable: energyBalance.value >= 0,
    
    // Recommended action based on energy balance
    recommendation: (() => {
      if (energyBalance.value > 500) return "Increase speed - surplus energy";
      if (energyBalance.value > 0) return "Maintain current pace";
      if (energyBalance.value > -300) return "Reduce speed slightly";
      return "REDUCE SPEED IMMEDIATELY - unsustainable";
    })(),
    
    // Power efficiency (km/h per watt)
    efficiency: currentSpeed > 0 && currentPower > 0 ? 
      (currentSpeed / currentPower).toFixed(3) : 0
  };
});

// Alert functions
function dismissAlert(alertId) {
  dismissedAlerts.value.add(alertId);
  // Auto-clear dismissed alerts after 5 minutes
  setTimeout(() => {
    dismissedAlerts.value.delete(alertId);
  }, 300000);
}

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

/* Critical Alerts Styles */
.critical-alerts-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 400px;
}

.critical-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  border-left: 4px solid;
  animation: alertPulse 2s infinite;
}

.critical-alert.critical {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
  border-left-color: #ff4444;
}

.critical-alert.warning {
  background: rgba(255, 136, 0, 0.2);
  color: #ff8800;
  border-left-color: #ff8800;
}

.alert-icon {
  font-size: 1rem;
}

.alert-text {
  flex: 1;
}

.dismiss-btn {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.dismiss-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

@keyframes alertPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

/* Energy Overview Styles */
.energy-overview {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid #333;
  overflow-x: auto;
}

.energy-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid #444;
}

.strategy-card {
  min-width: 200px;
  align-items: flex-start;
  text-align: left;
}

.energy-label {
  font-size: 0.8rem;
  color: #bbb;
  margin-bottom: 4px;
  text-align: center;
}

.energy-value {
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 2px;
}

.energy-sub {
  font-size: 0.7rem;
  color: #888;
  text-align: center;
}

.strategy-text {
  font-size: 0.85rem;
  color: #fff;
  font-weight: 500;
  text-align: center;
  margin-top: 4px;
}

.energy-value.solar {
  color: #ffd700;
}

.energy-value.battery {
  color: #00aaff;
}

.energy-value.positive {
  color: #00ff88;
}

.energy-value.slight-positive {
  color: #88ff88;
}

.energy-value.negative {
  color: #ff8800;
}

.energy-value.critical {
  color: #ff4444;
  animation: criticalBlink 1s infinite;
}

.energy-value.efficiency {
  color: #88ff88;
}

@keyframes criticalBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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
  
  .energy-overview {
    flex-wrap: wrap;
    padding: 12px 16px;
  }
  
  .energy-card {
    min-width: 100px;
    padding: 8px;
  }
  
  .critical-alerts-bar {
    max-width: 300px;
  }
  
  .critical-alert {
    font-size: 0.8rem;
    padding: 4px 8px;
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
  
  .energy-overview {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 12px;
  }
  
  .energy-card {
    min-width: auto;
  }
  
  .strategy-card {
    grid-column: 1 / -1;
    min-width: auto;
    align-items: center;
    text-align: center;
  }
  
  .critical-alerts-bar {
    max-width: 100%;
  }
}
</style>
