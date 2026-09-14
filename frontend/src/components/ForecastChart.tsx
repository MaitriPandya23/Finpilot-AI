"use client";

import React, { useState } from "react";
import { Sparkles, ArrowRight, ShieldCheck } from "lucide-react";
import { ForecastData } from "../lib/api";

interface ForecastChartProps {
  forecast: ForecastData | null;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ forecast }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const points = forecast?.forecast_data || [];
  const minVal = Math.min(...points.map((p) => p.yhat_lower), 20000);
  const maxVal = Math.max(...points.map((p) => p.yhat_upper), 80000);
  const range = maxVal - minVal || 1;

  const svgWidth = 600;
  const svgHeight = 180;
  const padding = 20;

  // Compute SVG coordinates
  const coords = points.map((p, i) => {
    const x = padding + (i / Math.max(points.length - 1, 1)) * (svgWidth - padding * 2);
    const yHat = svgHeight - padding - ((p.yhat - minVal) / range) * (svgHeight - padding * 2);
    const yLower = svgHeight - padding - ((p.yhat_lower - minVal) / range) * (svgHeight - padding * 2);
    const yUpper = svgHeight - padding - ((p.yhat_upper - minVal) / range) * (svgHeight - padding * 2);
    return { x, yHat, yLower, yUpper, ...p };
  });

  // Generate Area path for confidence corridor (yUpper -> yLower reversed)
  const upperPath = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.yUpper}`).join(" ");
  const lowerPath = [...coords].reverse().map((c) => `L ${c.x} ${c.yLower}`).join(" ");
  const confidenceArea = `${upperPath} ${lowerPath} Z`;

  // Line path for yhat
  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.yHat}`).join(" ");

  const totalProjected = points.reduce((acc, curr) => acc + curr.yhat, 0);

  return (
    <div className="glass-panel" style={{ padding: "24px", height: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={18} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Prophet AI Revenue Forecast</h2>
            <span className="badge badge-moderate" style={{ fontSize: "0.68rem" }}>
              {forecast?.model_version || "Prophet v1.4"}
            </span>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Next 30-day projection with 95% Bayesian uncertainty corridor
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>30-Day Projected Total</div>
          <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--accent-cyan)" }}>
            ${(totalProjected / 1_000_000).toFixed(2)}M
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ position: "relative", width: "100%", overflow: "hidden" }}>
        {coords.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: `${svgHeight}px`, color: "var(--text-muted)" }}>
            Computing Prophet projections...
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: "100%", height: `${svgHeight}px`, overflow: "visible" }}
          >
            <defs>
              <linearGradient id="corridorGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {/* Shaded Confidence Interval */}
            <path d={confidenceArea} fill="url(#corridorGradient)" />

            {/* Boundary strokes */}
            <path
              d={coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.yUpper}`).join(" ")}
              stroke="rgba(6, 182, 212, 0.3)"
              strokeWidth="1"
              strokeDasharray="3 3"
              fill="none"
            />
            <path
              d={coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.yLower}`).join(" ")}
              stroke="rgba(6, 182, 212, 0.3)"
              strokeWidth="1"
              strokeDasharray="3 3"
              fill="none"
            />

            {/* Central Forecast Curve (yhat) */}
            <path d={linePath} fill="none" stroke="#06b6d4" strokeWidth="2.5" />

            {/* Interactive Data Nodes */}
            {coords.map((c, i) => (
              <circle
                key={i}
                cx={c.x}
                cy={c.yHat}
                r={hoveredIndex === i ? 5 : 2.5}
                fill="#ffffff"
                stroke="#06b6d4"
                strokeWidth="2"
                style={{ cursor: "pointer", transition: "r 0.15s ease" }}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            ))}
          </svg>
        )}

        {/* Dynamic Tooltip on Hover */}
        {hoveredIndex !== null && coords[hoveredIndex] && (
          <div style={{
            position: "absolute",
            top: "8px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(15, 23, 42, 0.95)",
            border: "1px solid var(--border-highlight)",
            padding: "8px 14px",
            borderRadius: "8px",
            fontSize: "0.75rem",
            display: "flex",
            gap: "16px",
            zIndex: 40,
            boxShadow: "0 6px 20px rgba(0,0,0,0.6)",
          }}>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Date: </span>
              <strong>{coords[hoveredIndex].date}</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Expected: </span>
              <strong style={{ color: "var(--accent-cyan)" }}>${coords[hoveredIndex].yhat.toLocaleString()}</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Range: </span>
              <span>${coords[hoveredIndex].yhat_lower.toLocaleString()} - ${coords[hoveredIndex].yhat_upper.toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      {/* Legend & Meta */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginTop: "12px",
        paddingTop: "8px",
        borderTop: "1px solid var(--border-subtle)",
        fontSize: "0.7rem",
        color: "var(--text-muted)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <div style={{ width: "12px", height: "3px", backgroundColor: "#06b6d4" }} />
            <span>Predicted (yhat)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <div style={{ width: "12px", height: "10px", backgroundColor: "rgba(6, 182, 212, 0.25)" }} />
            <span>95% Confidence Corridor</span>
          </div>
        </div>
        <span>Horizon: {forecast?.forecast_horizon_days || 30} Days Ahead</span>
      </div>
    </div>
  );
};
