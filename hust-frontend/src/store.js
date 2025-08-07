import { defineStore } from "pinia";
import { io } from "socket.io-client";
import axios from "axios";

export const useTelemStore = defineStore("telem", {
  state: () => ({
    raw: { battery_data: [], motor_data: [], mppt_data: [], vehicle_data: [] },
    live: true, // true = streaming, false = paused
    loading: false,
    error: null,
    lastFetch: null,
    connectionStatus: 'disconnected',
    retryCount: 0,
    maxRetries: 3,
    lastSuccessfulData: null, // Cache last successful data fetch
    hasEverConnected: false   // Track if we've ever successfully connected
  }),
  
  getters: {
    isStale: (state) => {
      if (!state.lastFetch) return true;
      return Date.now() - state.lastFetch > 30000; // 30 seconds
    },
    
    hasData: (state) => {
      return state.raw.battery_data.length > 0 || 
             state.raw.motor_data.length > 0 || 
             state.raw.mppt_data.length > 0 || 
             state.raw.vehicle_data.length > 0;
    },
    
    isConnected: (state) => state.connectionStatus === 'connected',
    
    totalDataPoints: (state) => {
      return state.raw.battery_data.length + 
             state.raw.motor_data.length + 
             state.raw.mppt_data.length + 
             state.raw.vehicle_data.length;
    }
  },
  
  actions: {
    async init() {
      console.log("🚀 Initializing telemetry store...");
      this.loading = true;
      this.error = null;
      
      try {
        await this.refresh();
        await this.initSocket();
        console.log("✅ Store initialized successfully");
      } catch (error) {
        console.error("❌ Failed to initialize store:", error);
        this.error = "Failed to initialize connection";
      } finally {
        this.loading = false;
      }
    },
    
    async initSocket() {
      try {
        this.socket = io(); // proxied
        
        this.socket.on("connect", () => {
          console.log("🔌 Socket connected");
          this.connectionStatus = 'connected';
          this.retryCount = 0;
          this.error = null;
        });
        
        this.socket.on("disconnect", (reason) => {
          console.log("🔌 Socket disconnected:", reason);
          this.connectionStatus = 'disconnected';
          
          if (reason === 'io server disconnect') {
            // Server initiated disconnect, try to reconnect
            this.socket.connect();
          }
        });
        
        this.socket.on("connect_error", (error) => {
          console.error("🔌 Socket connection error:", error);
          this.connectionStatus = 'error';
          this.error = "Connection error";
        });
        
        this.socket.on("new_data", (payload) => {
          if (this.live && payload) {
            this.raw = payload;
            this.lastSuccessfulData = payload; // Cache successful WebSocket data
            this.hasEverConnected = true;
            this.lastFetch = Date.now();
            this.error = null;
            console.log("📊 Received new data:", this.totalDataPoints, "points");
          }
        });
        
      } catch (error) {
        console.error("Failed to initialize socket:", error);
        this.connectionStatus = 'error';
        throw error;
      }
    },
    
    async refresh(limit = 20) {
      this.loading = true;
      this.error = null;
      
      try {
        console.log(`🔄 Refreshing data (limit: ${limit})...`);
        const { data } = await axios.get(`/data?limit=${limit}`);
        this.raw = data;
        this.lastSuccessfulData = data; // Cache successful data
        this.hasEverConnected = true;   // Mark successful connection
        this.lastFetch = Date.now();
        this.retryCount = 0;
        console.log("✅ Data refreshed:", this.totalDataPoints, "points");
      } catch (error) {
        console.error("❌ Failed to refresh data:", error);
        
        // Use cached data if available, otherwise show error
        if (this.lastSuccessfulData && this.hasEverConnected) {
          this.raw = this.lastSuccessfulData;
          this.error = "Connection lost - showing cached data";
          console.log("📦 Using cached data:", this.totalDataPoints, "points");
        } else {
          this.error = error.response?.data?.error || "Failed to connect to database";
        }
        
        // Retry logic
        if (this.retryCount < this.maxRetries) {
          this.retryCount++;
          console.log(`🔄 Retrying... (${this.retryCount}/${this.maxRetries})`);
          setTimeout(() => this.refresh(limit), 2000 * this.retryCount);
        }
        
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    toggleLive() {
      this.live = !this.live;
      console.log(`📡 Live mode ${this.live ? 'enabled' : 'disabled'}`);
      
      if (this.live && this.isStale) {
        // If we're turning live mode on and data is stale, refresh
        this.refresh();
      }
    },
    
    async retry() {
      console.log("🔄 Manual retry triggered");
      this.error = null;
      this.retryCount = 0;
      await this.refresh();
    },
    
    disconnect() {
      if (this.socket) {
        this.socket.disconnect();
        this.connectionStatus = 'disconnected';
      }
    }
  },
});
