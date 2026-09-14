"use client";

import React from "react";
import { Activity, Database, Server, RefreshCw, Zap, ShieldCheck } from "lucide-react";

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  lastUpdated: string;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading, lastUpdated }) => {
  return (
    <header style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      padding: "18px 28px",
      borderBottom: "1px solid var(--border-subtle)",
      background: "rgba(9, 13, 22, 0.8)",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 50,
    }}>
      {/* Brand Identity */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{
          width: "42px",
          height: "42px",
          borderRadius: "12px",
          background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 20px rgba(99, 102, 241, 0.5)",
        }}>
          <Zap size={24} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.25rem", fontWeight: 800, letterSpacing: "-0.02em" }}>
              Finpilot<span style={{ color: "var(--accent-cyan)" }}>.AI</span>
            </h1>
            <span className="badge badge-success" style={{ fontSize: "0.7rem", padding: "2px 8px" }}>
              v1.0 Live
            </span>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Enterprise Big Data BI & Predictive Intelligence Platform
          </p>
        </div>
      </div>

      {/* Pipeline Status Chips */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <Activity size={14} color="#10b981" />
          <span>Kafka: <strong>Streaming</strong></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <Server size={14} color="#6366f1" />
          <span>MinIO: <strong>Lakehouse</strong></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <Database size={14} color="#06b6d4" />
          <span>PostgreSQL: <strong>Star Schema</strong></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <ShieldCheck size={14} color="#f59e0b" />
          <span>AI Models: <strong>Active</strong></span>
        </div>

        {/* Action Button */}
        <button
          onClick={onRefresh}
          className="btn-secondary"
          disabled={isLoading}
          style={{ marginLeft: "8px" }}
          title={`Last updated: ${lastUpdated}`}
        >
          <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
          <span>{isLoading ? "Refreshing..." : "Sync Pipeline"}</span>
        </button>
      </div>
    </header>
  );
};
