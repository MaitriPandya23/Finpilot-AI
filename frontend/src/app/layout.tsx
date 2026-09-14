import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Finpilot-AI | Big Data BI & Predictive Intelligence",
  description: "Executive analytics, Meta Prophet revenue forecasting, and Isolation Forest anomaly detection for enterprise retail.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
