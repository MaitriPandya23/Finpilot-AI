"use client";

import React from "react";
import { Lightbulb, ArrowUpRight, Zap, CheckCircle2 } from "lucide-react";
import { RecommendationsData } from "../lib/api";

interface RecommendationsPanelProps {
  recommendations: RecommendationsData | null;
  isLoading?: boolean;
}

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations, isLoading = false }) => {
  const items = recommendations?.recommendations || [];
  const isDemo = Boolean(recommendations?.is_demo);

  return (
    <div className="glass-panel" style={{ padding: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Lightbulb size={18} color="var(--accent-amber)" />
          <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>AI Prescriptive Intelligence</h2>
          <span className="badge badge-warning" style={{ fontSize: "0.68rem" }}>
            {isLoading ? "..." : `${items.length} Actions`}
          </span>
          {isDemo && (
            <span className="badge badge-moderate" style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
              Curated Baseline
            </span>
          )}
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Synthesized by Finpilot BI Engine
        </span>
      </div>

      {/* Action Cards Grid */}
      {isLoading ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: "210px",
                borderRadius: "12px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                animation: "pulse 1.5s infinite",
              }}
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div style={{ padding: "36px 0", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
            <Lightbulb size={24} color="rgba(255,255,255,0.2)" />
            <span>No prescriptive recommendations generated yet</span>
            <span style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.3)" }}>
              AI engine will generate operational optimization directives when transactions are recorded
            </span>
          </div>
        </div>
      ) : (
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
                    <span className={`badge ${priorityBadge}`} style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                      {rec.priority}
                    </span>
                  </div>

                  <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "8px", lineHeight: "1.35", color: "var(--text-primary)" }}>
                    {rec.title}
                  </h3>

                  <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                    {rec.description}
                  </p>
                </div>

                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  paddingTop: "12px",
                  borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                }}>
                  <div>
                    <div style={{ fontSize: "0.7rem", color: "var(--accent-emerald)", fontWeight: 700 }}>
                      {rec.impact}
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>
                      Metric: {rec.metric}
                    </div>
                  </div>

                  <button
                    className="btn-secondary"
                    style={{ fontSize: "0.72rem", padding: "4px 10px" }}
                    onClick={() => alert(`Action Dispatched: ${rec.action_label}\nDirective ID: ${rec.id}`)}
                  >
                    <span>{rec.action_label}</span>
                    <ArrowUpRight size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
