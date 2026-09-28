"""
Finpilot-AI Historical Trends BI Endpoints
Provides time-series aggregations (daily, weekly, monthly) of revenue and transaction volume.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta
import numpy as np

from ..database import get_db
from ..schemas import TrendsResponse, TrendPoint

router = APIRouter(prefix="", tags=["Trends"])


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    timeframe: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Retrieves chronological sales and order volume trends for interactive charts."""
    try:
        # Check if database has any sales records globally
        has_any_data = db.execute(text("SELECT 1 FROM fact_sales LIMIT 1;")).scalar() is not None

        # If database is freshly initialized or completely empty, provide rich demo baseline
        if not has_any_data:
            end_date = datetime.now().date()
            points = []
            base_rev = 32000.0

            # Scale step size and baseline revenue according to requested timeframe
            if timeframe == "monthly":
                step_days = 30
                multiplier = 28.0
            elif timeframe == "weekly":
                step_days = 7
                multiplier = 6.8
            else:
                step_days = 1
                multiplier = 1.0

            for i in range(limit - 1, -1, -1):
                dt = end_date - timedelta(days=i * step_days)
                # Seasonality and noise
                dow = dt.weekday()
                seasonality = 1.35 if dow in [4, 5] and timeframe == "daily" else 1.05
                noise = np.random.uniform(0.92, 1.12)
                rev = round(base_rev * multiplier * (1 + (limit - i) * 0.003) * seasonality * noise, 2)
                orders = int(rev / np.random.uniform(92.0, 115.0))

                date_label = (
                    dt.strftime("%Y-%m")
                    if timeframe == "monthly"
                    else dt.strftime("%Y-%m-%d")
                )

                points.append(
                    TrendPoint(
                        date=date_label,
                        revenue=rev,
                        order_count=orders,
                        avg_order_value=round(rev / max(orders, 1), 2),
                    )
                )

            return TrendsResponse(
                timeframe=timeframe,
                data_points=points,
                total_points=len(points),
                is_demo=True,
            )

        # Build date grouping expression based on requested timeframe
        if timeframe == "monthly":
            date_expr = "TO_CHAR(d.date_actual, 'YYYY-MM')"
        elif timeframe == "weekly":
            date_expr = "TO_CHAR(DATE_TRUNC('week', d.date_actual), 'YYYY-MM-DD')"
        else:
            date_expr = "d.date_actual::text"

        sql = f"""
            SELECT
                {date_expr} AS date_str,
                COALESCE(SUM(f.total_amount), 0.0) AS period_rev,
                COUNT(f.sales_key) AS period_orders
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY {date_expr}
            ORDER BY date_str DESC
            LIMIT :limit;
        """
        rows = db.execute(text(sql), {"limit": limit}).fetchall()

        if rows and len(rows) > 0:
            # Sort chronologically for chart display
            rows = sorted(rows, key=lambda x: x[0])
            points = [
                TrendPoint(
                    date=r[0],
                    revenue=round(float(r[1]), 2),
                    order_count=int(r[2]),
                    avg_order_value=round(float(r[1]) / max(int(r[2]), 1), 2),
                )
                for r in rows
            ]
            return TrendsResponse(
                timeframe=timeframe,
                data_points=points,
                total_points=len(points),
                is_demo=False,
            )

        # Database is populated, but no records matched the query parameters
        return TrendsResponse(
            timeframe=timeframe,
            data_points=[],
            total_points=0,
            is_demo=False,
        )

    except Exception as e:
        print(f"Error fetching trends: {e}")
        return TrendsResponse(timeframe=timeframe, data_points=[], total_points=0, is_demo=True)
