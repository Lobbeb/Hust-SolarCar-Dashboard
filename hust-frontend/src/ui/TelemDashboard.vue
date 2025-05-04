<template>
  <div class="shell">
    <!-- ===== header ===== -->
    <header>
      <h1>HUST Solar Car Dashboard</h1>
      <!-- Paus / Start -->
      <button class="pause" @click="liveFlag = !liveFlag">
        {{ liveFlag ? "⏸ Pause" : "▶ Start" }}
      </button>

      <!-- Tidsfönster -->
      <select v-model="limit" class="range">
        <option :value="20">20 points</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
      </select>
    </header>

    <!-- ========= Innehåll ========= -->
    <main class="grid">
      <MetricPanel title="Battery" :metrics="battery" />
      <MetricPanel title="Motor" :metrics="motor" />
      <MetricPanel title="MPPT" :metrics="mppt" />
      <MetricPanel title="Vehicle" :metrics="vehicle" />
    </main>
  </div>
</template>

<script setup>
import { ref, provide } from "vue";
import MetricPanel from "./MetricPanel.vue";

/* live-flagg + tidsfönster delas ut via provide */
const liveFlag = ref(true);
const limit = ref(20);
provide("liveFlag", liveFlag);
provide("limit", limit);

/* metrik-listor */
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
}

/* ---------- header ---------- */
header {
  background: #0009;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 12px 24px;
  box-shadow: 0 2px 6px #0007;
  position: sticky;
  top: 0;
  z-index: 10;
  justify-content: center;
}
h1 {
  margin: 0;
  font-size: 1.25rem;
}
.pause {
  background: var(--brand-soft);
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
}
.pause:hover {
  background: var(--brand);
}
.range {
  background: #2b2b2b;
  color: #fff;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
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
}
@media (max-width: 480px) {
  main.grid {
    grid-template-columns: 1fr;
  }
}
</style>
