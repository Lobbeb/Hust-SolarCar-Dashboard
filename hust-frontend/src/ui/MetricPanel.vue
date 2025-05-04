<template>
  <section class="card" @mouseover="hover = true" @mouseleave="hover = false">
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
      <button class="dl" @click="downloadCsv">⬇</button>
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

      <!-- Snitt + trendpil -->
      <div class="stat">
        <span class="lbl">Snitt</span>
        <span>{{ stats.avg }}</span>
        <span v-if="deltaSign" :class="deltaClass">{{ deltaSign }}</span>
      </div>

      <!-- Senast uppdaterad -->
      <div class="stat">
        <span class="lbl">Senast</span> <span>{{ lastTs }}</span>
      </div>

      <!-- Dynamisk varning baserat på medel + 3×sd -->
      <div class="stat" v-if="showWarning">
        <span class="warn-icon">⚠️</span>
      </div>
    </footer>
  </section>
</template>

<script setup>
import { ref, computed } from "vue";
import LiveChart from "./LiveChart.vue";

const props = defineProps({
  title: String,
  metrics: Array,
});

// valt mätvärde + label
const currentKey = ref(props.metrics[0].key);
const currentLabel = computed(
  () => props.metrics.find((m) => m.key === currentKey.value)?.label
);

// data från LiveChart
const series = ref([]);
const chartLabels = ref([]);

// live-värdet + färg
const latest = computed(() => series.value.at(-1) ?? "–");
const liveClass = computed(() =>
  latest.value !== "–" && latest.value > 0 ? "ok" : "warn"
);

// beräkna min/max/avg
const stats = computed(() => {
  const arr = series.value.map(Number);
  if (!arr.length) return { min: "–", max: "–", avg: "–" };
  const min = Math.min(...arr).toFixed(1);
  const max = Math.max(...arr).toFixed(1);
  const avg = (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1);
  return { min, max, avg };
});

// trendpil på slutet
const deltaSign = computed(() => {
  if (series.value.length < 2) return "";
  return series.value.at(-1) > series.value.at(-2)
    ? "▲"
    : series.value.at(-1) < series.value.at(-2)
    ? "▼"
    : "";
});
const deltaClass = computed(() => (deltaSign.value === "▲" ? "pos" : "neg"));

// senaste tidsstämpel
const lastTs = computed(() => {
  const t = chartLabels.value.at(-1);
  return t ? new Date(t).toLocaleTimeString() : "–";
});

// standardavvikelse (population)
const sd = computed(() => {
  const arr = series.value.map(Number);
  const n = arr.length;
  if (!n) return 0;
  const mean = arr.reduce((a, b) => a + b, 0) / n;
  const variance =
    arr.map((x) => (x - mean) ** 2).reduce((a, b) => a + b, 0) / n;
  return Math.sqrt(variance);
});

// varning om latest > avg + 3×sd
const showWarning = computed(() => {
  if (latest.value === "–") return false;
  return Number(latest.value) > Number(stats.value.avg) + 3 * sd.value;
});

// CSV-export
function downloadCsv() {
  const rows = chartLabels.value.map((t, i) => `${t},${series.value[i]}\n`);
  const blob = new Blob(["timestamp,value\n", ...rows], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement("a"), {
    href: url,
    download: `${currentKey.value}.csv`,
  }).click();
  URL.revokeObjectURL(url);
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
}
.card:hover {
  box-shadow: 0 6px 16px #0008;
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
