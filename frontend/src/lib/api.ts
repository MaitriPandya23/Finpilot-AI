/**
 * Finpilot-AI API Client
 * Resilient, typed HTTP client connecting Next.js dashboard to FastAPI backend.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CategoryRevenue {
  category: string;
  revenue: number;
  percentage: number;
  units_sold: number;
}

export interface ShopRevenue {
  shop_id: string;
  shop_name: string;
  tier: string;
  revenue: number;
  transactions: number;
}

export interface RevenueSummary {
  total_revenue: number;
  total_orders: number;
  avg_order_value: number;
  total_units_sold: number;
  growth_percentage: number;
  top_categories: CategoryRevenue[];
  top_shops: ShopRevenue[];
  is_demo?: boolean;
}

export interface TrendPoint {
  date: string;
  revenue: number;
  order_count: number;
  avg_order_value: number;
}

export interface TrendsData {
  timeframe: string;
  data_points: TrendPoint[];
  total_points: number;
  is_demo?: boolean;
}

export interface ForecastPoint {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export interface ForecastData {
  model_version: string;
  forecast_horizon_days: number;
  generated_at: string;
  forecast_data: ForecastPoint[];
  is_demo?: boolean;
}

export interface AnomalyItem {
  anomaly_id: number;
  transaction_id: string;
  date: string;
  shop_id: string;
  total_amount: number;
  anomaly_score: number;
  severity: "Critical" | "Warning" | "Moderate" | string;
  reason: string;
}

export interface AnomaliesData {
  total_anomalies: number;
  critical_count: number;
  warning_count: number;
  items: AnomalyItem[];
  is_demo?: boolean;
}

export interface RecommendationItem {
  id: string;
  category: string;
  title: string;
  description: string;
  impact: string;
  priority: "Critical" | "High" | "Medium" | "Low" | string;
  metric: string;
  action_label: string;
}

export interface RecommendationsData {
  generated_at: string;
  recommendations: RecommendationItem[];
  is_demo?: boolean;
}

export interface HealthData {
  status: string;
  timestamp: string;
  database: string;
  version: string;
}

/**
 * Generic helper to handle fetch with timeout & status validation
 */
async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(options.headers || {}),
      },
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const errorText = await res.text().catch(() => "Unknown error");
      throw new Error(`API error (${res.status}): ${errorText}`);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    console.error(`[API Client] Error requesting ${url}:`, err.message || err);
    throw err;
  }
}

export async function fetchRevenueSummary(): Promise<RevenueSummary> {
  return apiFetch<RevenueSummary>("/revenue");
}

export async function fetchTrends(timeframe = "daily", limit = 30): Promise<TrendsData> {
  return apiFetch<TrendsData>(`/trends?timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`);
}

export async function fetchForecast(horizon_days = 30): Promise<ForecastData> {
  return apiFetch<ForecastData>(`/forecast?horizon_days=${horizon_days}`);
}

export async function fetchAnomalies(severity?: string, limit = 50): Promise<AnomaliesData> {
  const query = new URLSearchParams();
  if (severity) query.append("severity", severity);
  if (limit) query.append("limit", limit.toString());
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<AnomaliesData>(`/anomalies${queryString}`);
}

export async function fetchRecommendations(): Promise<RecommendationsData> {
  return apiFetch<RecommendationsData>("/recommendations");
}

export async function fetchHealth(): Promise<HealthData> {
  return apiFetch<HealthData>("/health");
}
