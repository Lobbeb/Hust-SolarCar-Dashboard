<template>
  <div class="plot-box">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject } from "vue";
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Tooltip,
} from "chart.js";
import axios from "axios";
import { io } from "socket.io-client";

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Tooltip
);

/* v-models uppåt */
const modelValues = defineModel({ type: Array, default: () => [] });
const modelLabels = defineModel("labels", { type: Array, default: () => [] });

/* props + injects */
const props = defineProps({ metric: String });
const limit = inject("limit", ref(20));

/* refs / vars */
const canvas = ref(null);
let chart,
  socket,
  buffer = [];
let latestId = 0; // för att filtrera dubblettpushar

/* ----------- hjälp­funktioner ----------- */
function whichTable(key) {
  if (key.startsWith("battery_")) return "battery_data";
  if (key.startsWith("motor_")) return "motor_data";
  if (key.startsWith("MPPT")) return "mppt_data";
  return "vehicle_data";
}

/* rita serie + medellinje + autoscale */
function draw(values, labels) {
  /* glidande medel 5 punkter */
  const smooth = values.map((_, i, arr) => {
    const s = arr.slice(Math.max(0, i - 4), i + 1);
    return s.reduce((a, b) => a + b, 0) / s.length;
  });

  modelValues.value = values;
  modelLabels.value = labels;

  chart.data.labels = labels;
  chart.data.datasets = [
    {
      label: props.metric,
      data: values,
      borderColor: "#4bc0c0",
      tension: 0.35,
      pointRadius: 2,
      borderWidth: 2,
    },
    {
      label: "Medel",
      data: smooth,
      borderColor: "#ffb703",
      borderDash: [6, 4],
      tension: 0.35,
      pointRadius: 0,
      borderWidth: 2,
    },
  ];

  /* autoskala Y (5 % marginal) */
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  chart.options.scales.y.suggestedMin = min - span * 0.05;
  chart.options.scales.y.suggestedMax = max + span * 0.05;

  chart.update("none", { resize: false });
}

/* full ersättning av bufferten (vid fetch/metric-byte) */
function plot(rows) {
  buffer = rows.slice(-limit.value);
  const labels = buffer.map((r) => r.timestamp);
  const values = buffer.map((r) => r[props.metric]);
  latestId = buffer.at(-1)?.id ?? latestId;
  draw(values, labels);
}

/* lägg till rader från Socket.IO (filtrera dubletter) */
function mergeAndPlot(rows) {
  if (!rows.length) return;
  const newest = rows[0].id; // pushar kommer DESC
  if (newest <= latestId) return; // inget nytt

  latestId = newest;
  buffer = [...buffer, ...rows].slice(-limit.value);
  const labels = buffer.map((r) => r.timestamp);
  const values = buffer.map((r) => r[props.metric]);

  /* visuellt blink: tjock linje 150 ms */
  chart.data.datasets[0].borderWidth = 4;
  draw(values, labels);
  setTimeout(() => {
    chart.data.datasets[0].borderWidth = 2;
    chart.update("none");
  }, 150);
}

/* ---------------- datahämtning ---------------- */
async function fetchInitial() {
  const { data } = await axios.get(`/data?limit=${limit.value}`);
  plot(data[whichTable(props.metric)] ?? []);
}

onMounted(async () => {
  chart = new Chart(canvas.value, {
    type: "line",
    data: { labels: [], datasets: [{ data: [] }, { data: [] }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: 8 },
      scales: {
        x: { display: false },
        y: {
          grace: "5%",
          ticks: { color: "#fff" },
          grid: { color: "rgba(255,255,255,.12)" },
        },
      },
      plugins: {
        legend: { display: true, labels: { color: "#fff", boxWidth: 12 } },
        tooltip: {
          enabled: true,
          backgroundColor: "#2b2b2baa",
          callbacks: {
            /* kortare tidformat HH:MM:SS */
            title: (ctx) => new Date(ctx[0].label).toLocaleTimeString(),
          },
        },
      },
    },
  });

  await fetchInitial();

  socket = io();
  socket.on("new_data", (payload) => {
    mergeAndPlot(payload[whichTable(props.metric)] ?? []);
  });
});

watch(() => props.metric, fetchInitial);
watch(limit, fetchInitial);

onBeforeUnmount(() => {
  chart?.destroy();
  socket?.disconnect();
});
</script>

<style scoped>
.plot-box {
  height: 260px;
  width: 100%;
  overflow: hidden;
  display: flex;
}
canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
