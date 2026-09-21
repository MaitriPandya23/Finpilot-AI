"use client";

import React from "react";
import { DollarSign, ShoppingBag, TrendingUp, AlertTriangle, ArrowUpRight } from "lucide-react";
import { RevenueSummary, AnomaliesData } from "../lib/api";

interface KPICardsProps {
  revenue: RevenueSummary | null;
  anomalies: AnomaliesData | null;
  isLoading?: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ revenue, anomalies, isLoading = false }) => {
  const formatCurrency = (val: number) => {
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}k`;
    return `$${val.toFixed(2)}`;
  };

  const isDemo = Boolean(revenue?.is_demo || anomalies?.is_demo);
  const hasNoData = revenue && revenue.total_orders === 0 && !revenue.is_demo;

  const cards = [
    {
      title: "Gross Revenue",
      value: hasNoData ? "$0.00" : revenue ? formatCurrency(revenue.total_revenue) : "$0.00",
      subtext: hasNoData
        ? "No transactions yet"
        : isDemo
        ? "Cold-start demo baseline"
        : `+${revenue?.growth_percentage || 0}% vs prev period`,
      isPositive: !hasNoData,
      icon: DollarSign,
      color: "#6366f1",
      glow: "rgba(99, 102, 241, 0.2)",
    },
    {
      title: "Total Transactions",
      value: hasNoData ? "0" : revenue ? revenue.total_orders.toLocaleString() : "0",
      subtext: hasNoData
        ? "Awaiting Kafka stream"
        : `${(revenue?.total_units_sold || 0).toLocaleString()} units sold`,
      isPositive: !hasNoData,
      icon: ShoppingBag,
      color: "#06b6d4",
      glow: "rgba(6, 182, 212, 0.2)",
    },
    {
      title: "Average Order Value",
      value: hasNoData ? "$0.00" : revenue ? `$${revenue.avg_order_value.toFixed(2)}` : "$0.00",
      subtext: hasNoData ? "No basket data" : isDemo ? "Projected baseline AOV" : "Dynamic basket mean",
      isPositive: !hasNoData,
      icon: TrendingUp,
      color: "#10b981",
      glow: "rgba(16, 185, 129, 0.2)",
    },
    {
      title: "Flagged Anomalies",
      value: anomalies ? anomalies.total_anomalies.toString() : "0",
      subtext: anomalies
        ? `${anomalies.critical_count} Critical / ${anomalies.warning_count} Warning`
        : "Stream monitor idle",
      isPositive: anomalies ? anomalies.critical_count === 0 : true,
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

        if (isLoading) {
          return (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: "20px 24px",
                position: "relative",
                overflow: "hidden",
                minHeight: "135px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ width: "100px", height: "14px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
                <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "rgba(255,255,255,0.06)", animation: "pulse 1.5s infinite" }} />
              </div>
              <div style={{ width: "130px", height: "32px", borderRadius: "6px", background: "rgba(255,255,255,0.06)", marginBottom: "12px", animation: "pulse 1.5s infinite" }} />
              <div style={{ width: "90px", height: "12px", borderRadius: "4px", background: "rgba(255,255,255,0.04)", animation: "pulse 1.5s infinite" }} />
            </div>
          );
        }

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
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 500 }}>
                  {card.title}
                </span>
                {isDemo && (
                  <span style={{
                    fontSize: "0.62rem",
                    padding: "1px 5px",
                    borderRadius: "4px",
                    background: "rgba(245, 158, 11, 0.15)",
                    color: "var(--accent-amber)",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                    fontWeight: 600,
                  }}>
                    Demo
                  </span>
                )}
              </div>
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
                {card.isPositive && !hasNoData && <ArrowUpRight size={14} />}
                {card.subtext}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
