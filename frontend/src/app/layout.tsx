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
    <html lang="en" className="dark" style={{ backgroundColor: "#090d16", color: "#f8fafc", colorScheme: "dark" }}>
      <head>
        <meta name="color-scheme" content="dark" />
        <meta name="theme-color" content="#090d16" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap"
        />
      </head>
      <body style={{ backgroundColor: "#090d16", color: "#f8fafc", minHeight: "100vh", margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
