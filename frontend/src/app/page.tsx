"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { KPICards } from "../components/KPICards";
import { TrendsChart } from "../components/TrendsChart";
import { ForecastChart } from "../components/ForecastChart";
import { CategoryBreakdown } from "../components/CategoryBreakdown";
import { AnomalyTable } from "../components/AnomalyTable";
import { RecommendationsPanel } from "../components/RecommendationsPanel";
import {
  fetchRevenueSummary,
  fetchTrends,
  fetchForecast,
  fetchAnomalies,
  fetchRecommendations,
  RevenueSummary,
  TrendsData,
  ForecastData,
  AnomaliesData,
  RecommendationsData,
} from "../lib/api";

export default function DashboardPage() {
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [anomalies, setAnomalies] = useState<AnomaliesData | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationsData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadAllData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [revData, trendsData, forecastData, anomalyData, recData] = await Promise.all([
        fetchRevenueSummary(),
        fetchTrends("daily", 30),
        fetchForecast(30),
        fetchAnomalies(),
        fetchRecommendations(),
      ]);

      setRevenue(revData);
      setTrends(trendsData);
      setForecast(forecastData);
      setAnomalies(anomalyData);
      setRecommendations(recData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      console.error("Error loading dashboard metrics:", err);
      setErrorMessage(
        `Unable to reach backend API at ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}. Ensure Docker backend service is running.`
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const isDemoMode = Boolean(
    revenue?.is_demo ||
    trends?.is_demo ||
    forecast?.is_demo ||
    anomalies?.is_demo ||
    recommendations?.is_demo
  );

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Navigation */}
      <Header
        onRefresh={loadAllData}
        isLoading={isLoading}
        lastUpdated={lastUpdated}
        isDemo={isDemoMode}
      />

      {/* Main Content Dashboard Container */}
      <main style={{ flex: 1, padding: "24px 28px", maxWidth: "1600px", margin: "0 auto", width: "100%" }}>
        {/* Error Alert if API unreachable */}
        {errorMessage && (
          <div style={{
            background: "rgba(244, 63, 94, 0.12)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "10px",
            padding: "12px 18px",
            marginBottom: "20px",
            fontSize: "0.82rem",
            color: "var(--accent-rose)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span>⚠️ {errorMessage}</span>
            <button
              onClick={loadAllData}
              className="btn-secondary"
              style={{ fontSize: "0.72rem", padding: "4px 10px" }}
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Informative Cold-Start Notice */}
        {!isLoading && !errorMessage && isDemoMode && (
          <div style={{
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.22)",
            borderRadius: "10px",
            padding: "10px 18px",
            marginBottom: "20px",
            fontSize: "0.8rem",
            color: "var(--accent-amber)",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}>
            <span style={{ fontSize: "1rem" }}>ℹ️</span>
            <span>
              <strong>Cold-Start Simulation Active:</strong> PostgreSQL database is currently awaiting live transaction ingestion. You are previewing synthetic baseline KPIs and predictive simulations. Live database results take priority automatically as data streams in.
            </span>
          </div>
        )}

        {/* Row 1: Executive KPI Banner */}
        <KPICards revenue={revenue} anomalies={anomalies} isLoading={isLoading} />

        {/* Row 2: Historical Trends & Prophet AI Forecast */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
          gap: "24px",
          marginBottom: "24px",
        }}>
          <TrendsChart data={trends} isLoading={isLoading} />
          <ForecastChart forecast={forecast} isLoading={isLoading} />
        </div>

        {/* Row 3: Category Breakdown & Top Store Performance */}
        <div style={{ marginBottom: "24px" }}>
          <CategoryBreakdown revenue={revenue} isLoading={isLoading} />
        </div>

        {/* Row 4: Isolation Forest Anomaly Audit Feed */}
        <div style={{ marginBottom: "24px" }}>
          <AnomalyTable anomalies={anomalies} isLoading={isLoading} />
        </div>

        {/* Row 5: AI Prescriptive Intelligence */}
        <div style={{ marginBottom: "24px" }}>
          <RecommendationsPanel recommendations={recommendations} isLoading={isLoading} />
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: "center",
        padding: "20px",
        borderTop: "1px solid var(--border-subtle)",
        color: "var(--text-muted)",
        fontSize: "0.75rem",
      }}>
        Finpilot-AI • Big Data BI Platform • Lakehouse Medallion Architecture (MinIO + PySpark + PostgreSQL + Prophet)
      </footer>
    </div>
  );
}
