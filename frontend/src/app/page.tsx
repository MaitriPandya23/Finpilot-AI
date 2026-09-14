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

  const loadAllData = async () => {
    setIsLoading(true);
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
    } catch (err) {
      console.error("Error loading dashboard metrics:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Navigation */}
      <Header onRefresh={loadAllData} isLoading={isLoading} lastUpdated={lastUpdated} />

      {/* Main Content Dashboard Container */}
      <main style={{ flex: 1, padding: "28px", maxWidth: "1600px", margin: "0 auto", width: "100%" }}>
        {/* Row 1: Executive KPI Banner */}
        <KPICards revenue={revenue} anomalies={anomalies} />

        {/* Row 2: Historical Trends & Prophet AI Forecast */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
          gap: "24px",
          marginBottom: "24px",
        }}>
          <TrendsChart data={trends} />
          <ForecastChart forecast={forecast} />
        </div>

        {/* Row 3: Category Breakdown & Top Store Performance */}
        <div style={{ marginBottom: "24px" }}>
          <CategoryBreakdown revenue={revenue} />
        </div>

        {/* Row 4: Isolation Forest Anomaly Audit Feed */}
        <div style={{ marginBottom: "24px" }}>
          <AnomalyTable anomalies={anomalies} />
        </div>

        {/* Row 5: AI Prescriptive Intelligence */}
        <div style={{ marginBottom: "24px" }}>
          <RecommendationsPanel recommendations={recommendations} />
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
