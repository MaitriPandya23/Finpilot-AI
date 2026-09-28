"use client";

import React from "react";
import { PieChart, Store, MapPin } from "lucide-react";
import { RevenueSummary } from "../lib/api";

interface CategoryBreakdownProps {
  revenue: RevenueSummary | null;
  isLoading?: boolean;
}

export const CategoryBreakdown: React.FC<CategoryBreakdownProps> = ({ revenue, isLoading = false }) => {
  const categories = revenue?.top_categories || [];
  const shops = revenue?.top_shops || [];

  const categoryColors: Record<string, string> = {
    Electronics: "#6366f1",
    Apparel: "#06b6d4",
    "Home & Kitchen": "#10b981",
    "Beauty & Care": "#ec4899",
    "Beauty & Personal Care": "#ec4899",
    Groceries: "#f59e0b",
    "Groceries & Gourmet": "#f59e0b",
    Sports: "#8b5cf6",
    "Sports & Outdoors": "#8b5cf6",
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "24px" }}>
      {/* Category Mix */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
          <PieChart size={18} color="var(--accent-primary)" />
          <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Merchandising Category Mix</h2>
        </div>

        {isLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div style={{ width: "90px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                  <div style={{ width: "60px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                </div>
                <div style={{ width: "100%", height: "6px", borderRadius: "9999px", background: "rgba(255,255,255,0.04)", animation: "pulse 1.5s infinite" }} />
              </div>
            ))}
          </div>
        ) : categories.length === 0 ? (
          <div style={{ padding: "30px 0", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            No category transactions recorded in warehouse yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {categories.map((cat, idx) => {
              const color = categoryColors[cat.category] || "#6366f1";
              return (
                <div key={idx}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: "4px" }}>
                    <span style={{ fontWeight: 600 }}>{cat.category}</span>
                    <span style={{ color: "var(--text-secondary)" }}>
                      ${(cat.revenue / 1_000).toFixed(0)}k ({cat.percentage}%)
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255, 255, 255, 0.06)", borderRadius: "9999px", overflow: "hidden" }}>
                    <div style={{
                      width: `${cat.percentage}%`,
                      height: "100%",
                      backgroundColor: color,
                      borderRadius: "9999px",
                      transition: "width 0.4s ease",
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Top Performing Stores */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
          <Store size={18} color="var(--accent-emerald)" />
          <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>Top Retail Locations</h2>
        </div>

        {isLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                style={{
                  height: "52px",
                  borderRadius: "8px",
                  background: "rgba(255,255,255,0.03)",
                  animation: "pulse 1.5s infinite",
                }}
              />
            ))}
          </div>
        ) : shops.length === 0 ? (
          <div style={{ padding: "30px 0", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            No retail store performance records available yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {shops.slice(0, 5).map((shop, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  background: "rgba(255, 255, 255, 0.02)",
                  borderRadius: "8px",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", width: "18px" }}>
                    #{idx + 1}
                  </span>
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>{shop.shop_name}</div>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                      <MapPin size={10} />
                      <span>{shop.shop_id} • {shop.transactions.toLocaleString()} txns</span>
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                    ${(shop.revenue / 1000).toFixed(1)}k
                  </div>
                  <span className="badge badge-moderate" style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                    {shop.tier}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
