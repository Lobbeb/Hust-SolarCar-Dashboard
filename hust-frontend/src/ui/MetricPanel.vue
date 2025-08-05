<template>
  <section class="card" @mouseover="hover = true" @mouseleave="hover = false">
    <!-- Loading overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading data...</p>
    </div>
    
    <!-- Error state -->
    <div v-if="hasError" class="error-state">
      <span class="error-icon">⚠️</span>
      <p>{{ errorMessage }}</p>
      <button @click="retry" class="retry-btn">Retry</button>
    </div>
    
    <!-- Connection status indicator -->
    <div v-if="!isConnected" class="connection-status">
      <span class="status-dot offline"></span>
      <small>Offline</small>
    </div>
    <div v-else class="connection-status">
      <span class="status-dot online"></span>
      <small>Live</small>
    </div>

    <header>
      <div class="title">
        <h2>{{ title }}</h2>
        <small class="sub">{{ currentLabel }}</small>
      </div>

      <select v-model="currentKey">
        <option v-for="m in metrics" :key="m.key" :value="m.key">
          {{ m.label }}
        </option>
      </select>

      <span :class="['live-val', liveClass]">{{ latest }}</span>
      <button class="dl" @click="downloadCsv" :disabled="!hasData">⬇</button>
    </header>

    <LiveChart
      :metric="currentKey"
      v-model="series"
      v-model:labels="chartLabels"
    />

    <footer>
      <!-- Min / Max -->
      <div class="stat">
        <span class="lbl">Min</span> <span>{{ stats.min }}</span>
      </div>
      <div class="stat">
        <span class="lbl">Max</span> <span>{{ stats.max }}</span>
      </div>

      <!-- Average + trend arrow -->
      <div class="stat">
        <span class="lbl">Avg</span>
        <span>{{ stats.avg }}</span>
        <span v-if="deltaSign" :class="deltaClass">{{ deltaSign }}</span>
      </div>

      <!-- Last updated -->
      <div class="stat">
        <span class="lbl">Last</span> <span>{{ lastTs }}</span>
      </div>

      <!-- Dynamic warning based on average + 3×sd -->
      <div class="stat" v-if="showWarning">
        <span class="warn-icon">⚠️</span>
      </div>
      
      <!-- Data staleness indicator -->
      <div class="stat" v-if="isStale">
        <span class="stale-icon">🕐</span>
        <small>Stale data</small>
      </div>
    </footer>
  </section>
</template>

<script setup>
import { ref, computed, inject } from "vue";
import LiveChart from "./LiveChart.vue";

const props = defineProps({
  title: String,
  metrics: Array,
});

// Store injection for error states
const store = inject('telemStore', null);

// selected metric + label
const currentKey = ref(props.metrics[0].key);
const currentLabel = computed(
  () => props.metrics.find((m) => m.key === currentKey.value)?.label
);

// data from LiveChart
const series = ref([]);
const chartLabels = ref([]);

// Store-derived states
const isLoading = computed(() => store?.loading || false);
const hasError = computed(() => !!store?.error);
const errorMessage = computed(() => store?.error || 'Unknown error');
const isConnected = computed(() => store?.isConnected || false);
const isStale = computed(() => store?.isStale || false);
const hasData = computed(() => series.value.length > 0);

// live value + color
const latest = computed(() => series.value.at(-1) ?? "–");
const liveClass = computed(() =>
  latest.value !== "–" && latest.value > 0 ? "ok" : "warn"
);

// calculate min/max/avg
const stats = computed(() => {
  const arr = series.value.map(Number);
  if (!arr.length) return { min: "–", max: "–", avg: "–" };
  const min = Math.min(...arr).toFixed(1);
  const max = Math.max(...arr).toFixed(1);
  const avg = (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1);
  return { min, max, avg };
});

// trend arrow at the end
const deltaSign = computed(() => {
  if (series.value.length < 2) return "";
  return series.value.at(-1) > series.value.at(-2)
    ? "▲"
    : series.value.at(-1) < series.value.at(-2)
    ? "▼"
    : "";
});
const deltaClass = computed(() => (deltaSign.value === "▲" ? "pos" : "neg"));

// latest timestamp
const lastTs = computed(() => {
  const t = chartLabels.value.at(-1);
  return t ? new Date(t).toLocaleTimeString() : "–";
});

// standard deviation (population)
const sd = computed(() => {
  const arr = series.value.map(Number);
  const n = arr.length;
  if (!n) return 0;
  const mean = arr.reduce((a, b) => a + b, 0) / n;
  const variance =
    arr.map((x) => (x - mean) ** 2).reduce((a, b) => a + b, 0) / n;
  return Math.sqrt(variance);
});

// warning if latest > avg + 3×sd
const showWarning = computed(() => {
  if (latest.value === "–") return false;
  return Number(latest.value) > Number(stats.value.avg) + 3 * sd.value;
});

// Retry function
function retry() {
  if (store && store.retry) {
    store.retry();
  }
}

// CSV export
function downloadCsv() {
  if (!hasData.value) return;
  
  try {
    const rows = chartLabels.value.map((t, i) => `${t},${series.value[i]}\n`);
    const blob = new Blob(["timestamp,value\n", ...rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement("a"), {
      href: url,
      download: `${currentKey.value}_${new Date().toISOString().split('T')[0]}.csv`,
    }).click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download CSV:', error);
  }
}
</script>

<style scoped>
.card {
  background: var(--panel);
  border-radius: 8px;
  box-shadow: 0 4px 12px #0006;
  padding: 16px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.25s;
  position: relative;
}
.card:hover {
  box-shadow: 0 6px 16px #0008;
}

/* Loading overlay */
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
  z-index: 10;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--brand-soft, #444);
  border-top: 4px solid var(--brand, #00ff88);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error state */
.error-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(139, 0, 0, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  z-index: 10;
  color: white;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 10px;
}

.retry-btn {
  background: #ff4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  margin-top: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #ff6666;
}

/* Connection status */
.connection-status {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: #bbb;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: #00ff88;
  box-shadow: 0 0 4px #00ff88;
}

.status-dot.offline {
  background: #ff4444;
  box-shadow: 0 0 4px #ff4444;
}

header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 6px;
}
.title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
h2 {
  margin: 0;
  font-size: 1.05rem;
}
.sub {
  color: #bbb;
  font-size: 0.75rem;
  margin-top: 2px;
}

select {
  margin-left: auto;
  background: #2b2b2b;
  color: #fff;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
}

.live-val {
  font-size: 0.9rem;
}
.live-val.ok {
  color: var(--brand);
}
.live-val.warn {
  color: #ff5252;
}

.dl {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 1rem;
  cursor: pointer;
}
.dl:hover {
  color: #ffd27a;
}

footer {
  margin-top: 8px;
  font-size: 0.8rem;
  color: #bbb;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}
.stat {
  display: flex;
  gap: 4px;
  align-items: center;
}
.lbl {
  color: #888;
  font-weight: bold;
}
.pos {
  color: var(--brand);
}
.neg {
  color: #ff5252;
}
.warn-icon {
  font-size: 1.1rem;
  color: #ff5252;
}
</style>
