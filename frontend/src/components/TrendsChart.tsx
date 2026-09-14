"use client";

import React, { useState } from "react";
import { BarChart3, Calendar } from "lucide-react";
import { TrendsData } from "../lib/api";

interface TrendsChartProps {
  data: TrendsData | null;
}

export const TrendsChart: React.FC<TrendsChartProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<"7D" | "30D">("30D");
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const rawPoints = data?.data_points || [];
  const points = activeTab === "7D" ? rawPoints.slice(-7) : rawPoints.slice(-30);

  const maxRevenue = Math.max(...points.map((p) => p.revenue), 1000);
  const chartHeight = 180;

  return (
    <div className="glass-panel" style={{ padding: "24px", height: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <BarChart3 size={18} color="var(--accent-primary)" />
            <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Historical Revenue Trends</h2>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Daily revenue totals and order volume momentum
          </p>
        </div>

        {/* Timeframe Filter Tabs */}
        <div style={{
          display: "flex",
          background: "rgba(255, 255, 255, 0.05)",
          borderRadius: "8px",
          padding: "3px",
          border: "1px solid var(--border-subtle)",
        }}>
          {(["7D", "30D"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                background: activeTab === tab ? "var(--accent-primary)" : "transparent",
                color: activeTab === tab ? "#ffffff" : "var(--text-secondary)",
                border: "none",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Interactive Chart */}
      <div style={{ position: "relative", width: "100%", height: `${chartHeight + 40}px` }}>
        {points.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)" }}>
            Loading trend data...
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "flex-end", gap: "6px", height: `${chartHeight}px`, width: "100%" }}>
            {points.map((p, idx) => {
              const heightPercent = Math.max((p.revenue / maxRevenue) * 100, 5);
              const isHovered = hoveredIdx === idx;
              return (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-end",
                    position: "relative",
                  }}
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                >
                  {/* Tooltip */}
                  {isHovered && (
                    <div style={{
                      position: "absolute",
                      bottom: `${heightPercent + 10}%`,
                      left: "50%",
                      transform: "translateX(-50%)",
                      background: "rgba(15, 23, 42, 0.95)",
                      border: "1px solid var(--border-highlight)",
                      padding: "6px 10px",
                      borderRadius: "6px",
                      fontSize: "0.7rem",
                      whiteSpace: "nowrap",
                      zIndex: 30,
                      boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
                    }}>
                      <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>${p.revenue.toLocaleString()}</div>
                      <div style={{ color: "var(--text-muted)" }}>{p.date} • {p.order_count} orders</div>
                      <div style={{ color: "var(--accent-emerald)" }}>AOV: ${p.avg_order_value}</div>
                    </div>
                  )}

                  {/* Bar */}
                  <div style={{
                    width: "100%",
                    height: `${heightPercent}%`,
                    background: isHovered
                      ? "linear-gradient(180deg, #818cf8 0%, #4f46e5 100%)"
                      : "linear-gradient(180deg, #6366f1 0%, rgba(99, 102, 241, 0.35) 100%)",
                    borderRadius: "4px 4px 1px 1px",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    boxShadow: isHovered ? "0 0 12px rgba(99, 102, 241, 0.6)" : "none",
                  }} />
                </div>
              );
            })}
          </div>
        )}

        {/* X-Axis labels */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "10px",
          paddingTop: "6px",
          borderTop: "1px solid var(--border-subtle)",
          fontSize: "0.7rem",
          color: "var(--text-muted)",
        }}>
          <span>{points[0]?.date || "Start"}</span>
          <span>{points[Math.floor(points.length / 2)]?.date || "Mid"}</span>
          <span>{points[points.length - 1]?.date || "Latest"}</span>
        </div>
      </div>
    </div>
  );
};
