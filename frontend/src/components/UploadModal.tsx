"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  X,
  Download,
  Database,
  ArrowRight,
  Layers,
  Sparkles,
} from "lucide-react";
import { uploadCSVFile, getSampleCsvUrl, UploadResponse } from "../lib/api";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.toLowerCase().endsWith(".csv") || file.name.toLowerCase().endsWith(".txt")) {
        setSelectedFile(file);
        setUploadResult(null);
        setErrorMessage(null);
      } else {
        setErrorMessage("Please select a valid CSV file (.csv).");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadResult(null);
      setErrorMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMessage(null);
    try {
      const result = await uploadCSVFile(selectedFile);
      setUploadResult(result);
      if (result.success) {
        onUploadSuccess();
      } else {
        setErrorMessage(result.message || "CSV validation failed. Please check constraints.");
      }
    } catch (err: any) {
      console.error("Upload error:", err);
      setErrorMessage(err.message || "Failed to connect to backend upload service.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isUploading) {
          onClose();
        }
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "760px",
          maxHeight: "90vh",
          overflowY: "auto",
          background: "linear-gradient(180deg, rgba(20, 26, 42, 0.95) 0%, rgba(12, 16, 28, 0.98) 100%)",
          border: "1px solid var(--border-highlight)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(99, 102, 241, 0.2)",
          padding: "28px",
          position: "relative",
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={isUploading}
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            borderRadius: "8px",
            width: "32px",
            height: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          title="Close"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "20px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px rgba(99, 102, 241, 0.4)",
            }}
          >
            <UploadCloud size={24} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.01em" }}>
              Upload Retail Transactions CSV
            </h2>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Ingest business sales records into the Kimball star schema warehouse with automated data quality checks.
            </p>
          </div>
        </div>

        {/* Dropzone */}
        {!uploadResult && (
          <div>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${
                  isDragging
                    ? "var(--accent-primary)"
                    : selectedFile
                    ? "var(--accent-emerald)"
                    : "rgba(255, 255, 255, 0.15)"
                }`,
                borderRadius: "14px",
                padding: "36px 20px",
                textAlign: "center",
                cursor: "pointer",
                background: isDragging
                  ? "rgba(99, 102, 241, 0.12)"
                  : selectedFile
                  ? "rgba(16, 185, 129, 0.05)"
                  : "rgba(255, 255, 255, 0.02)",
                transition: "all 0.2s ease",
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv,text/plain"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />

              <div
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "50%",
                  background: selectedFile
                    ? "rgba(16, 185, 129, 0.15)"
                    : "rgba(99, 102, 241, 0.15)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 14px",
                }}
              >
                {selectedFile ? (
                  <FileSpreadsheet size={28} color="#10b981" />
                ) : (
                  <UploadCloud size={28} color="#6366f1" />
                )}
              </div>

              {selectedFile ? (
                <div>
                  <p style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-primary)" }}>
                    {selectedFile.name}
                  </p>
                  <p style={{ fontSize: "0.8rem", color: "var(--accent-emerald)", marginTop: "4px" }}>
                    {formatFileSize(selectedFile.size)} • Ready for validation and warehouse loading
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReset();
                    }}
                    style={{
                      marginTop: "12px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-muted)",
                      fontSize: "0.75rem",
                      cursor: "pointer",
                      textDecoration: "underline",
                    }}
                  >
                    Select different file
                  </button>
                </div>
              ) : (
                <div>
                  <p style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-primary)" }}>
                    Drag & Drop your CSV file here, or <span style={{ color: "var(--accent-cyan)" }}>browse</span>
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
                    Required columns: <code>transaction_id, date, product, quantity, unit_price, total</code>
                  </p>
                </div>
              )}
            </div>

            {/* Quick Helper / Sample Download */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "14px",
                padding: "10px 14px",
                background: "rgba(255, 255, 255, 0.03)",
                borderRadius: "8px",
                fontSize: "0.75rem",
                color: "var(--text-secondary)",
              }}
            >
              <span>Need a sample file to test?</span>
              <a
                href={getSampleCsvUrl()}
                download="finpilot_sample_retail_transactions.csv"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "var(--accent-cyan)",
                  textDecoration: "none",
                  fontWeight: 600,
                }}
              >
                <Download size={14} />
                Download Sample CSV
              </a>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && !uploadResult?.success && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px 16px",
              background: "rgba(244, 63, 94, 0.12)",
              border: "1px solid rgba(244, 63, 94, 0.35)",
              borderRadius: "10px",
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              color: "var(--accent-rose)",
              fontSize: "0.82rem",
            }}
          >
            <XCircle size={18} style={{ flexShrink: 0, marginTop: "2px" }} />
            <div>
              <p style={{ fontWeight: 600 }}>Validation Error</p>
              <p style={{ marginTop: "2px" }}>{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Upload Result Details */}
        {uploadResult && (
          <div style={{ marginTop: "16px" }}>
            {/* Status Banner */}
            <div
              style={{
                padding: "16px 20px",
                background: uploadResult.success
                  ? "rgba(16, 185, 129, 0.12)"
                  : "rgba(244, 63, 94, 0.12)",
                border: `1px solid ${
                  uploadResult.success ? "rgba(16, 185, 129, 0.35)" : "rgba(244, 63, 94, 0.35)"
                }`,
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "20px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                {uploadResult.success ? (
                  <CheckCircle2 size={24} color="#10b981" />
                ) : (
                  <AlertTriangle size={24} color="#f43f5e" />
                )}
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <h3 style={{ fontSize: "0.95rem", fontWeight: 700 }}>
                      {uploadResult.success ? "Data Ingestion Succeeded" : "Ingestion Failed"}
                    </h3>
                    {uploadResult.schema_detected && (
                      <span
                        className="badge badge-moderate"
                        style={{ fontSize: "0.65rem", padding: "1px 6px" }}
                      >
                        {uploadResult.schema_detected}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                    {uploadResult.message}
                  </p>
                </div>
              </div>

              {/* Quality Score Meter */}
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "block" }}>
                  Data Quality Score
                </span>
                <span
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: 800,
                    color:
                      uploadResult.quality_score >= 90
                        ? "var(--accent-emerald)"
                        : uploadResult.quality_score >= 70
                        ? "var(--accent-amber)"
                        : "var(--accent-rose)",
                  }}
                >
                  {uploadResult.quality_score}%
                </span>
              </div>
            </div>

            {/* Ingestion Metric Badges (Comprehensive 6-card grid) */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
                gap: "10px",
                marginBottom: "20px",
              }}
            >
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Detected Format</span>
                <p style={{ fontSize: "0.85rem", fontWeight: 700, marginTop: "4px", color: "var(--accent-cyan)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {uploadResult.schema_detected || "Canonical"}
                </p>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Total Rows</span>
                <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px" }}>
                  {uploadResult.total_rows.toLocaleString()}
                </p>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Valid Rows</span>
                <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px", color: "var(--accent-emerald)" }}>
                  {uploadResult.valid_rows.toLocaleString()}
                </p>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Invalid Rows</span>
                <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px", color: (uploadResult.rejected_rows ?? 0) > 0 ? "var(--accent-rose)" : "var(--text-secondary)" }}>
                  {(uploadResult.rejected_rows ?? (uploadResult.total_rows - uploadResult.valid_rows)).toLocaleString()}
                </p>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Warehouse Inserted</span>
                <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px", color: "var(--accent-cyan)" }}>
                  {uploadResult.inserted_rows.toLocaleString()}
                </p>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px",
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Duplicates Skipped</span>
                <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px", color: "var(--accent-amber)" }}>
                  {uploadResult.duplicate_count.toLocaleString()}
                </p>
              </div>

              {(uploadResult.return_count ?? 0) > 0 && (
                <div
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "10px",
                    padding: "10px",
                    textAlign: "center",
                  }}
                >
                  <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Returns / Credit</span>
                  <p style={{ fontSize: "1rem", fontWeight: 700, marginTop: "2px", color: "var(--accent-rose)" }}>
                    {(uploadResult.return_count ?? 0).toLocaleString()}
                  </p>
                </div>
              )}
            </div>

            {/* Warnings list if any */}
            {uploadResult.warnings && uploadResult.warnings.length > 0 && (
              <div
                style={{
                  marginBottom: "20px",
                  padding: "12px 16px",
                  background: "rgba(245, 158, 11, 0.06)",
                  border: "1px solid rgba(245, 158, 11, 0.2)",
                  borderRadius: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <AlertTriangle size={14} color="#f59e0b" />
                  <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-amber)" }}>
                    Quality Notes & Adjustments ({uploadResult.warnings.length})
                  </span>
                </div>
                <ul
                  style={{
                    paddingLeft: "18px",
                    fontSize: "0.72rem",
                    color: "var(--text-secondary)",
                    lineHeight: "1.5",
                  }}
                >
                  {uploadResult.warnings.slice(0, 4).map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                  {uploadResult.warnings.length > 4 && (
                    <li style={{ color: "var(--text-muted)" }}>
                      +{uploadResult.warnings.length - 4} more notes
                    </li>
                  )}
                </ul>
              </div>
            )}

            {/* Sample Preview Table */}
            {uploadResult.sample_preview && uploadResult.sample_preview.length > 0 && (
              <div style={{ marginBottom: "20px" }}>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    display: "block",
                    marginBottom: "8px",
                  }}
                >
                  Parsed Sample Preview (First 5 Rows)
                </span>
                <div
                  style={{
                    overflowX: "auto",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "0.72rem",
                      textAlign: "left",
                    }}
                  >
                    <thead>
                      <tr style={{ background: "rgba(255, 255, 255, 0.05)" }}>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>TXN ID</th>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Date</th>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Product</th>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Category</th>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Qty</th>
                        <th style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploadResult.sample_preview.map((row, i) => (
                        <tr
                          key={i}
                          style={{
                            borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                            background: i % 2 === 0 ? "transparent" : "rgba(255, 255, 255, 0.01)",
                          }}
                        >
                          <td style={{ padding: "8px 10px", fontFamily: "monospace" }}>
                            {row.transaction_id || "-"}
                          </td>
                          <td style={{ padding: "8px 10px", color: "var(--text-secondary)" }}>
                            {row.date || "-"}
                          </td>
                          <td style={{ padding: "8px 10px", fontWeight: 500 }}>
                            {row.product || "-"}
                          </td>
                          <td style={{ padding: "8px 10px", color: "var(--text-secondary)" }}>
                            {row.category || "-"}
                          </td>
                          <td style={{ padding: "8px 10px" }}>{row.quantity || "-"}</td>
                          <td style={{ padding: "8px 10px", color: "var(--accent-emerald)" }}>
                            ${parseFloat(row.total || 0).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal Actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: "12px",
            marginTop: "24px",
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "18px",
          }}
        >
          {uploadResult ? (
            <>
              <button
                type="button"
                onClick={handleReset}
                className="btn-secondary"
                style={{ fontSize: "0.85rem" }}
              >
                Upload Another File
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-primary"
                style={{ fontSize: "0.85rem" }}
              >
                <span>View Dashboard</span>
                <ArrowRight size={14} />
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
                disabled={isUploading}
                style={{ fontSize: "0.85rem" }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="btn-primary"
                style={{
                  fontSize: "0.85rem",
                  opacity: !selectedFile || isUploading ? 0.6 : 1,
                  cursor: !selectedFile || isUploading ? "not-allowed" : "pointer",
                }}
              >
                {isUploading ? (
                  <>
                    <Database size={16} className="animate-spin" />
                    <span>Validating & Ingesting...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud size={16} />
                    <span>Upload & Process CSV</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
