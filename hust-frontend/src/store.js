import { defineStore } from "pinia";
import { io } from "socket.io-client";
import axios from "axios";

export const useTelemStore = defineStore("telem", {
  state: () => ({
    raw: { battery_data: [], motor_data: [], mppt_data: [], vehicle_data: [] },
    live: true, // true = streaming, false = paused
  }),
  actions: {
    async init() {
      await this.refresh();
      this.socket = io(); // proxied
      this.socket.on("new_data", (payload) => {
        if (this.live) this.raw = payload;
      });
    },
    async refresh(limit = 20) {
      const { data } = await axios.get(`/data?limit=${limit}`);
      this.raw = data;
    },
    toggleLive() {
      this.live = !this.live;
    },
  },
});
