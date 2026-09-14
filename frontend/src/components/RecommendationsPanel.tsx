"use client";

import React from "react";
import { Lightbulb, ArrowUpRight, Zap, CheckCircle2 } from "lucide-react";
import { RecommendationsData } from "../lib/api";

interface RecommendationsPanelProps {
  recommendations: RecommendationsData | null;
}

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => {
  const items = recommendations?.recommendations || [];

  return (
    <div className="glass-panel" style={{ padding: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Lightbulb size={18} color="var(--accent-amber)" />
          <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>AI Prescriptive Intelligence</h2>
          <span className="badge badge-warning" style={{ fontSize: "0.68rem" }}>
            {items.length} Actions
          </span>
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Synthesized by Finpilot BI Engine
        </span>
      </div>

      {/* Action Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
        {items.map((rec) => {
          const priorityBadge =
            rec.priority === "Critical"
              ? "badge-critical"
              : rec.priority === "High"
              ? "badge-warning"
              : "badge-moderate";

          return (
            <div
              key={rec.id}
              style={{
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "12px",
                padding: "16px 18px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "12px",
                transition: "border-color 0.2s ease, transform 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--border-highlight)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-subtle)";
                e.currentTarget.style.transform = "none";
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", fontWeight: 600 }}>
                    {rec.category}
                  </span>
                  <span className={`badge ${priorityBadge}`} style={{ fontSize: "0.65rem", padding: "1px 7px" }}>
                    {rec.priority} Priority
                  </span>
                </div>

                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
                  {rec.title}
                </h3>
                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                  {rec.description}
                </p>
              </div>

              <div>
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 10px",
                  background: "rgba(99, 102, 241, 0.08)",
                  borderRadius: "8px",
                  marginBottom: "12px",
                  border: "1px solid rgba(99, 102, 241, 0.15)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--accent-cyan)", fontWeight: 600 }}>
                    <Zap size={13} />
                    <span>{rec.metric}</span>
                  </div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#ffffff" }}>
                    {rec.impact}
                  </span>
                </div>

                <button
                  className="btn-primary"
                  style={{ width: "100%", justifyContent: "center", fontSize: "0.8rem", padding: "7px 12px" }}
                  onClick={() => alert(`Triggered action: ${rec.action_label}`)}
                >
                  <span>{rec.action_label}</span>
                  <ArrowUpRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
