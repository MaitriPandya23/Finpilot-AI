"use client";

import React, { useState } from "react";
import { AlertOctagon, Filter, Eye, ShieldAlert } from "lucide-react";
import { AnomaliesData, AnomalyItem } from "../lib/api";

interface AnomalyTableProps {
  anomalies: AnomaliesData | null;
  isLoading?: boolean;
}

export const AnomalyTable: React.FC<AnomalyTableProps> = ({ anomalies, isLoading = false }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>("All");
  const items = anomalies?.items || [];
  const isDemo = Boolean(anomalies?.is_demo);

  const filteredItems = filterSeverity === "All"
    ? items
    : items.filter((i) => i.severity === filterSeverity);

  return (
    <div className="glass-panel" style={{ padding: "24px" }}>
      {/* Table Header Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={18} color="var(--accent-rose)" />
            <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Isolation Forest Anomaly Feed</h2>
            <span className="badge badge-critical" style={{ fontSize: "0.68rem" }}>
              {isLoading ? "..." : `${anomalies?.total_anomalies || 0} Flagged`}
            </span>
            {isDemo && (
              <span className="badge badge-warning" style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                Cold-Start Samples
              </span>
            )}
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Real-time transaction outlier detection and risk diagnosis
          </p>
        </div>

        {/* Severity Filter */}
        <div style={{ display: "flex", gap: "6px" }}>
          {["All", "Critical", "Warning", "Moderate"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              style={{
                background: filterSeverity === sev ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.04)",
                color: filterSeverity === sev ? "#ffffff" : "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "4px 10px",
                fontSize: "0.75rem",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Table View */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}>
              <th style={{ padding: "10px 12px" }}>Transaction ID</th>
              <th style={{ padding: "10px 12px" }}>Date</th>
              <th style={{ padding: "10px 12px" }}>Shop</th>
              <th style={{ padding: "10px 12px" }}>Amount</th>
              <th style={{ padding: "10px 12px" }}>Score</th>
              <th style={{ padding: "10px 12px" }}>Severity</th>
              <th style={{ padding: "10px 12px" }}>Diagnostic Reason</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [1, 2, 3, 4, 5].map((i) => (
                <tr key={i} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "110px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "80px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "70px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "75px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "50px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "65px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  </td>
                  <td style={{ padding: "14px 12px" }}>
                    <div style={{ width: "220px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.04)", animation: "pulse 1.5s infinite" }} />
                  </td>
                </tr>
              ))
            ) : filteredItems.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: "36px 12px", textAlign: "center", color: "var(--text-muted)" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                    <AlertOctagon size={24} color="rgba(255,255,255,0.2)" />
                    <span>No anomaly events matching filter criteria</span>
                    <span style={{ fontSize: "0.72rem", color: "rgba(255,255,255,0.3)" }}>
                      All stream transactions are currently evaluated within standard risk parameters
                    </span>
                  </div>
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => {
                const badgeClass =
                  item.severity === "Critical"
                    ? "badge-critical"
                    : item.severity === "Warning"
                    ? "badge-warning"
                    : "badge-moderate";

                return (
                  <tr
                    key={item.anomaly_id}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                      transition: "background-color 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.03)")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    <td style={{ padding: "12px", fontFamily: "monospace", fontWeight: 600, color: "var(--text-primary)" }}>
                      {item.transaction_id}
                    </td>
                    <td style={{ padding: "12px", color: "var(--text-muted)" }}>{item.date}</td>
                    <td style={{ padding: "12px", fontWeight: 500 }}>{item.shop_id}</td>
                    <td style={{ padding: "12px", fontWeight: 700, color: item.total_amount > 5000 ? "var(--accent-rose)" : "var(--text-primary)" }}>
                      ${item.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: "12px", fontFamily: "monospace", color: "var(--text-muted)" }}>
                      {item.anomaly_score.toFixed(4)}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span className={`badge ${badgeClass}`}>{item.severity}</span>
                    </td>
                    <td style={{ padding: "12px", color: "var(--text-secondary)", maxWidth: "380px" }}>
                      {item.reason}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
