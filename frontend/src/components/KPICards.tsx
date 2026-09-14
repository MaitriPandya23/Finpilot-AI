"use client";

import React from "react";
import { DollarSign, ShoppingBag, TrendingUp, AlertTriangle, ArrowUpRight } from "lucide-react";
import { RevenueSummary, AnomaliesData } from "../lib/api";

interface KPICardsProps {
  revenue: RevenueSummary | null;
  anomalies: AnomaliesData | null;
}

export const KPICards: React.FC<KPICardsProps> = ({ revenue, anomalies }) => {
  const formatCurrency = (val: number) => {
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}k`;
    return `$${val.toFixed(2)}`;
  };

  const cards = [
    {
      title: "Gross Revenue",
      value: revenue ? formatCurrency(revenue.total_revenue) : "$3.84M",
      subtext: "+16.4% vs prev period",
      isPositive: true,
      icon: DollarSign,
      color: "#6366f1",
      glow: "rgba(99, 102, 241, 0.2)",
    },
    {
      title: "Total Transactions",
      value: revenue ? revenue.total_orders.toLocaleString() : "38,120",
      subtext: `${revenue ? revenue.total_units_sold.toLocaleString() : "84,910"} units sold`,
      isPositive: true,
      icon: ShoppingBag,
      color: "#06b6d4",
      glow: "rgba(6, 182, 212, 0.2)",
    },
    {
      title: "Average Order Value",
      value: revenue ? `$${revenue.avg_order_value.toFixed(2)}` : "$100.79",
      subtext: "+4.8% basket expansion",
      isPositive: true,
      icon: TrendingUp,
      color: "#10b981",
      glow: "rgba(16, 185, 129, 0.2)",
    },
    {
      title: "Flagged Anomalies",
      value: anomalies ? anomalies.total_anomalies.toString() : "5",
      subtext: `${anomalies ? anomalies.critical_count : 2} Critical / ${anomalies ? anomalies.warning_count : 2} Warning`,
      isPositive: false,
      icon: AlertTriangle,
      color: "#f43f5e",
      glow: "rgba(244, 63, 94, 0.2)",
    },
  ];

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
      gap: "20px",
      marginBottom: "24px",
    }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="glass-panel"
            style={{
              padding: "20px 24px",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Top Row: Title & Icon */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 500 }}>
                {card.title}
              </span>
              <div style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                backgroundColor: card.glow,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}>
                <Icon size={18} color={card.color} />
              </div>
            </div>

            {/* Metric Value */}
            <div style={{
              fontSize: "1.85rem",
              fontWeight: 800,
              letterSpacing: "-0.03em",
              margin: "12px 0 6px 0",
              color: "var(--text-primary)",
            }}>
              {card.value}
            </div>

            {/* Bottom Row: Subtext / Delta badge */}
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem" }}>
              <span style={{
                color: card.isPositive ? "#10b981" : "#f43f5e",
                display: "inline-flex",
                alignItems: "center",
                fontWeight: 600,
              }}>
                {card.isPositive && <ArrowUpRight size={14} />}
                {card.subtext}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
