
import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  LayoutDashboard, Database, Upload, GitBranch, GitCompareArrows,
  Activity, ShieldCheck, Bell, FileText, Settings, LogOut, Menu, X,
  FileSpreadsheet, CheckCircle, AlertCircle, RefreshCw,
  AlertTriangle, Check, Download, Play, Eye
} from "lucide-react";

import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, BarChart, Bar
} from "recharts";


import Login from "./login.jsx";
import API, {
  getPipelineHistory,
  getPipelineRunDetails
} from "./services/api";

import "./App.css";

// --------------------------------------------------
// CONSTANTS
// --------------------------------------------------

const navItems = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Data Explorer", icon: Database },
  { name: "Upload Data", icon: Upload },
  { name: "Pipeline Runs", icon: GitBranch },
  { name: "Baseline Comparison", icon: GitCompareArrows },
  { name: "Data Quality", icon: ShieldCheck },
  { name: "Alerts", icon: Bell },
  { name: "Reports", icon: FileText }
];

const formatNumber = value =>
  Number(value ?? 0).toLocaleString();

const getTotal = (run, primary, fallback) =>
  Number(run?.[primary] ?? run?.[fallback] ?? 0);

const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map(item => item.msg || "Invalid input").join(", ");
  }

  return error?.message || fallback;
};

// Normalize API history fields so every component uses one format.
function normalizeRun(run = {}) {
  return {
    ...run,
    run_id: run.run_id || run.id || "",
    filename: run.filename || "Unknown dataset",
    status: run.status || "Unknown",
    total_records: getTotal(run, "total_records", "total_rows"),
    valid_records: getTotal(run, "valid_records", "valid_rows"),
    rejected_records: getTotal(run, "rejected_records", "rejected_rows"),
    missing_value_records: getTotal(
      run,
      "missing_value_records",
      "missing_rows"
    ),
    duplicate_records: getTotal(
      run,
      "duplicate_records",
      "duplicate_rows"
    ),
    quality_score: Number(run.quality_score ?? 0)
  };
}

function extractHistory(response) {
  const rows =
    response?.history ??
    response?.data?.history ??
    response?.data?.data?.history ??
    (Array.isArray(response) ? response : []);

  return Array.isArray(rows)
    ? rows.map(normalizeRun)
    : [];
}

function isCompleted(status) {
  return String(status || "").trim().toLowerCase() === "completed";
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString();
}

// --------------------------------------------------
// COMMON COMPONENTS
// --------------------------------------------------

function MetricCard({ title, value, icon: Icon, color, subtitle }) {
  return (
    <div className="quality-stat-card">
      <div className={`stat-icon ${color || "blue"}`}>
        <Icon size={21} />
      </div>
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{subtitle}</small>
    </div>
  );
}

function EmptyPage({ title, message }) {
  return (
    <div className="dashboard-content">
      <div className="panel quality-empty">
        <Database size={40} />
        <h2>{title}</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}

function ErrorMessage({ children }) {
  if (!children) return null;

  return (
    <div className="upload-error">
      <AlertCircle size={19} />
      {children}
    </div>
  );
}

function LoadingMessage({ message }) {
  return (
    <div className="panel quality-empty">
      <RefreshCw size={28} />
      <p>{message}</p>
    </div>
  );
}

// --------------------------------------------------
// REPORT DOWNLOAD
// --------------------------------------------------

async function downloadReport(runId, reportType) {
  if (!runId) {
    alert("Pipeline run ID is missing.");
    return;
  }

  if (!["valid", "rejected"].includes(reportType)) {
    alert("Invalid report type.");
    return;
  }

  try {
    const response = await API.get(
      `/upload/pipeline/report/${encodeURIComponent(runId)}/${reportType}`,
      { responseType: "blob" }
    );

    const blob = new Blob([response.data], {
      type: "text/csv;charset=utf-8;"
    });

    // Detect JSON error responses returned as blobs.
    if (blob.type.includes("application/json")) {
      const errorText = await blob.text();

      try {
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.detail || "Report download failed.");
      } catch (error) {
        if (error.message !== "Report download failed.") throw error;
        throw error;
      }
    }

    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = blobUrl;
    link.download = `${reportType}_records_${runId}.csv`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    // Revoke after the browser has started the download.
    window.setTimeout(() => {
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
  } catch (error) {
    alert(getErrorMessage(error, `Unable to download ${reportType} report.`));
  }
}

// --------------------------------------------------
// REJECTED RECORD PREVIEW
// --------------------------------------------------

function RejectedPreview({ rows = [] }) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return <p>No rejected record preview is available.</p>;
  }

  const columns = Object.keys(rows[0] || {});

  if (columns.length === 0) {
    return <p>No rejected record preview is available.</p>;
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(column => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map(column => (
                <td key={column}>{String(row?.[column] ?? "—")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --------------------------------------------------
// PIPELINE SUMMARY
// --------------------------------------------------

function PipelineSummary({ result }) {
  if (!result) return null;

  const run = normalizeRun(result);
  const quality = Math.min(100, Math.max(0, run.quality_score));

  const rejectedPreview =
    result.rejected_preview ||
    result.rejected_records_preview ||
    [];

  return (
    <div className="panel pipeline-summary">
      <div className="panel-heading">
        <div>
          <h3>
            <CheckCircle size={19} />
            Pipeline Execution Result
          </h3>
          <p>{run.filename}</p>
        </div>

        <span className={`quality-status ${
          isCompleted(run.status) ? "good" : "warning"
        }`}>
          {run.status}
        </span>
      </div>

      <div className="quality-stats-grid">
        <MetricCard
          title="Quality Score"
          value={`${quality.toFixed(2)}%`}
          icon={ShieldCheck}
          color="green"
          subtitle="Pipeline quality score"
        />

        <MetricCard
          title="Total Records"
          value={formatNumber(run.total_records)}
          icon={Database}
          color="blue"
          subtitle="Records processed"
        />

        <MetricCard
          title="Valid Records"
          value={formatNumber(run.valid_records)}
          icon={CheckCircle}
          color="green"
          subtitle="Accepted records"
        />

        <MetricCard
          title="Rejected Records"
          value={formatNumber(run.rejected_records)}
          icon={AlertTriangle}
          color="orange"
          subtitle="Records requiring review"
        />
      </div>

      <div className="quality-progress-panel">
        <div className="panel-heading">
          <div>
            <h3>Pipeline Quality Score</h3>
            <p>Valid records divided by total records</p>
          </div>
          <strong>{quality.toFixed(2)}%</strong>
        </div>

        <div className="quality-progress-track">
          <div
            className="quality-progress-fill"
            style={{ width: `${quality}%` }}
          />
        </div>
      </div>

      <div className="upload-stats">
        <div className="upload-stat">
          <span>Rows with Missing Values</span>
          <strong>{formatNumber(run.missing_value_records)}</strong>
        </div>

        <div className="upload-stat">
          <span>Duplicate Rows</span>
          <strong>{formatNumber(run.duplicate_records)}</strong>
        </div>
      </div>

      <h3>Rejected Records Preview</h3>
      <RejectedPreview rows={rejectedPreview} />

      <div className="report-downloads">
        <button
          className="upload-action-btn"
          onClick={() => downloadReport(run.run_id, "valid")}
          disabled={!run.run_id}
        >
          <Download size={18} /> Download Valid CSV
        </button>

        <button
          className="upload-action-btn secondary-action"
          onClick={() => downloadReport(run.run_id, "rejected")}
          disabled={!run.run_id}
        >
          <Download size={18} /> Download Rejected CSV
        </button>
      </div>
    </div>
  );
}

// --------------------------------------------------
// UPLOAD DATA
// --------------------------------------------------

function UploadData({
  onUploadSuccess,
  onPipelineSuccess,
  dataset,
  pipelineResult
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(dataset);
  const [error, setError] = useState("");
  const [pipelineError, setPipelineError] = useState("");

  useEffect(() => {
    setResult(dataset);
  }, [dataset]);

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files are supported.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError("Maximum file size is 20 MB.");
      return;
    }

    setUploading(true);
    setError("");
    setPipelineError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await API.post("/upload/csv", formData);

      setResult(response.data);
      onUploadSuccess(response.data);
    } catch (err) {
      setError(getErrorMessage(err, "CSV upload failed."));
    } finally {
      setUploading(false);
    }
  };

  const handlePipeline = async () => {
    if (!result?.filename) {
      setPipelineError("Please upload a CSV file first.");
      return;
    }

    setRunning(true);
    setPipelineError("");

    try {
      const response = await API.post(
        "/upload/pipeline/run",
        null,
        { params: { filename: result.filename } }
      );

      await onPipelineSuccess(response.data);
    } catch (err) {
      setPipelineError(
        getErrorMessage(err, "Pipeline execution failed.")
      );
    } finally {
      setRunning(false);
    }
  };

  const totalMissing = Object.values(result?.missing_values || {})
    .reduce((sum, value) => sum + Number(value || 0), 0);

  const missingEntries = Object.entries(result?.missing_values || {});
  const columns = result?.column_names || [];

  return (
    <div className="dashboard-content">
      <div className="panel upload-panel">
        <div className="panel-heading">
          <div>
            <h3>Upload Dataset</h3>
            <p>Upload a CSV file for data quality monitoring.</p>
          </div>
          <FileSpreadsheet size={28} />
        </div>

        <div className="upload-dropzone">
          <Upload size={42} />
          <h3>Select CSV Dataset</h3>
          <p>Choose a CSV file (Maximum 20 MB).</p>

          <input
            type="file"
            accept=".csv,text/csv"
            onChange={event => {
              setFile(event.target.files?.[0] || null);
              setError("");
              setPipelineError("");
            }}
          />

          {file && (
            <div className="selected-file">
              <FileSpreadsheet size={20} />
              <span>{file.name}</span>
              <small>{(file.size / 1024).toFixed(2)} KB</small>
            </div>
          )}

          <button
            className="upload-action-btn"
            onClick={handleUpload}
            disabled={uploading || !file}
          >
            {uploading
              ? <><RefreshCw size={18} /> Uploading...</>
              : <><Upload size={18} /> Upload Dataset</>}
          </button>
        </div>

        <ErrorMessage>{error}</ErrorMessage>

        {result && (
          <div className="upload-results">
            <div className="upload-success">
              <CheckCircle size={21} />
              {result.message || "CSV uploaded successfully"}
            </div>

            <h3>Dataset Summary</h3>

            <div className="upload-stats">
              <div className="upload-stat">
                <span>Total Rows</span>
                <strong>{formatNumber(result.rows)}</strong>
              </div>

              <div className="upload-stat">
                <span>Total Columns</span>
                <strong>{formatNumber(result.columns)}</strong>
              </div>

              <div className="upload-stat">
                <span>Missing Values</span>
                <strong>{formatNumber(totalMissing)}</strong>
              </div>

              <div className="upload-stat">
                <span>Duplicate Rows</span>
                <strong>{formatNumber(result.duplicate_rows)}</strong>
              </div>
            </div>

            <h3>Column Quality Report</h3>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Column Name</th>
                    <th>Missing Values</th>
                  </tr>
                </thead>

                <tbody>
                  {missingEntries.length > 0 ? (
                    missingEntries.map(([column, count]) => (
                      <tr key={column}>
                        <td>{column}</td>
                        <td>{formatNumber(count)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="2">No column quality information returned.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <h3>Data Preview</h3>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    {columns.map(column => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {(result.preview || []).map((row, index) => (
                    <tr key={index}>
                      {columns.map(column => (
                        <td key={column}>
                          {row?.[column] == null || row[column] === ""
                            ? "—"
                            : String(row[column])}
                        </td>
                      ))}
                    </tr>
                  ))}

                  {(!result.preview || result.preview.length === 0) && (
                    <tr>
                      <td colSpan={Math.max(columns.length, 1)}>
                        No preview records returned.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="pipeline-action-area">
              <div>
                <h3>Data Quality Pipeline</h3>
                <p>
                  Validate records, identify rejected rows
                  and generate reports.
                </p>
              </div>

              <button
                className="upload-action-btn"
                onClick={handlePipeline}
                disabled={running}
              >
                {running
                  ? <><RefreshCw size={18} /> Running...</>
                  : <><Play size={18} /> Run Pipeline</>}
              </button>
            </div>

            <ErrorMessage>{pipelineError}</ErrorMessage>
          </div>
        )}
      </div>

      {pipelineResult && (
        <PipelineSummary result={pipelineResult} />
      )}
    </div>
  );
}

// --------------------------------------------------
// BASELINE COMPARISON
// --------------------------------------------------

function BaselineComparison({ history = [] }) {
  const runs = history.filter(run => isCompleted(run.status));

  if (runs.length < 2) {
    return (
      <div className="dashboard-content">
        <div className="panel quality-empty">
          <GitCompareArrows size={42} />
          <h2>Baseline Comparison</h2>
          <p>
            You need at least two completed pipeline runs
            to compare results.
          </p>
          <p>
            Upload another CSV dataset and run the pipeline
            to create a comparison.
          </p>
          <small>{runs.length} of 2 required completed runs available.</small>
        </div>
      </div>
    );
  }

  const current = normalizeRun(runs[0]);
  const baseline = normalizeRun(runs[1]);

  const metrics = [
    {
      label: "Quality Score",
      old: baseline.quality_score,
      current: current.quality_score,
      suffix: "%",
      higher: true
    },
    {
      label: "Valid Records",
      old: baseline.valid_records,
      current: current.valid_records,
      suffix: "",
      higher: true
    },
    {
      label: "Rejected Records",
      old: baseline.rejected_records,
      current: current.rejected_records,
      suffix: "",
      higher: false
    },
    {
      label: "Missing Value Rows",
      old: baseline.missing_value_records,
      current: current.missing_value_records,
      suffix: "",
      higher: false
    },
    {
      label: "Duplicate Rows",
      old: baseline.duplicate_records,
      current: current.duplicate_records,
      suffix: "",
      higher: false
    }
  ];

  const scoreDifference = current.quality_score - baseline.quality_score;
  const improved = scoreDifference > 0;
  const unchanged = scoreDifference === 0;

  return (
    <div className="dashboard-content">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h3>
              <GitCompareArrows size={21} />
              Baseline Comparison
            </h3>
            <p>Compare your latest completed run with the previous run.</p>
          </div>

          <span className={`quality-status ${
            improved ? "good" : unchanged ? "" : "warning"
          }`}>
            {improved
              ? "Quality Improved"
              : unchanged
                ? "No Change"
                : "Quality Dropped"}
          </span>
        </div>

        <div className="upload-stats">
          <div className="upload-stat">
            <span>Baseline Dataset</span>
            <strong>{baseline.filename}</strong>
          </div>

          <div className="upload-stat">
            <span>Current Dataset</span>
            <strong>{current.filename}</strong>
          </div>
        </div>

        <div className="quality-stats-grid">
          <MetricCard
            title="Baseline Score"
            value={`${baseline.quality_score.toFixed(2)}%`}
            icon={ShieldCheck}
            color="blue"
            subtitle="Previous run"
          />

          <MetricCard
            title="Current Score"
            value={`${current.quality_score.toFixed(2)}%`}
            icon={ShieldCheck}
            color="green"
            subtitle="Latest run"
          />

          <MetricCard
            title="Score Difference"
            value={`${scoreDifference > 0 ? "+" : ""}${scoreDifference.toFixed(2)}%`}
            icon={Activity}
            color={improved ? "green" : "orange"}
            subtitle="Change from baseline"
          />
        </div>

        <h3>Metric-by-Metric Comparison</h3>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Baseline</th>
                <th>Current</th>
                <th>Difference</th>
                <th>Result</th>
              </tr>
            </thead>

            <tbody>
              {metrics.map(metric => {
                const difference = metric.current - metric.old;

                const isBetter = metric.higher
                  ? difference > 0
                  : difference < 0;

                const isSame = difference === 0;

                return (
                  <tr key={metric.label}>
                    <td>{metric.label}</td>
                    <td>{formatNumber(metric.old)}{metric.suffix}</td>
                    <td>{formatNumber(metric.current)}{metric.suffix}</td>
                    <td>
                      {difference > 0 ? "+" : ""}
                      {formatNumber(difference)}{metric.suffix}
                    </td>
                    <td>
                      <span className={
                        isSame || isBetter
                          ? "quality-cell-good"
                          : "quality-cell-warning"
                      }>
                        {isSame ? "No Change" : isBetter ? "Improved" : "Declined"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className={`quality-alert ${
          improved ? "good" : "warning"
        }`}>
          {improved
            ? <CheckCircle size={20} />
            : <AlertTriangle size={20} />}

          <div>
            <strong>
              {improved
                ? "Data Quality Improved"
                : unchanged
                  ? "Data Quality Unchanged"
                  : "Data Quality Needs Attention"}
            </strong>

            <p>
              {improved
                ? `Quality score improved by ${scoreDifference.toFixed(2)} percentage points compared with the previous run.`
                : unchanged
                  ? "The quality score is the same as the previous pipeline run."
                  : `Quality score decreased by ${Math.abs(scoreDifference).toFixed(2)} percentage points compared with the previous run.`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------
// DATA QUALITY
// --------------------------------------------------

function DataQuality({ dataset, pipelineResult }) {
  if (!dataset) {
    return (
      <EmptyPage
        title="Data Quality"
        message="Upload a CSV dataset to view quality metrics."
      />
    );
  }

  const missingValues = dataset.missing_values || {};

  const totalMissing = Object.values(missingValues)
    .reduce((sum, count) => sum + Number(count || 0), 0);

  const totalCells = Number(dataset.rows || 0) * Number(dataset.columns || 0);

  const completeness = totalCells > 0
    ? Math.max(0, Math.min(100, ((totalCells - totalMissing) / totalCells) * 100))
    : 0;

  const duplicateCount = Number(dataset.duplicate_rows || 0);
  const hasIssues = totalMissing > 0 || duplicateCount > 0;

  const chartData = Object.entries(missingValues).map(
    ([column, count]) => ({
      column,
      missing: Number(count)
    })
  );

  return (
    <div className="dashboard-content">
      <div className="quality-header panel">
        <div>
          <span className="quality-eyebrow">LATEST DATASET ANALYSIS</span>
          <h2>{dataset.filename}</h2>
          <p>Quality analysis of your uploaded CSV dataset.</p>
        </div>

        <span className={`quality-status ${hasIssues ? "warning" : "good"}`}>
          {hasIssues ? <AlertTriangle size={16} /> : <Check size={16} />}
          {hasIssues ? "Issues Detected" : "No Issues"}
        </span>
      </div>

      <div className="quality-stats-grid">
        <MetricCard
          title="Total Records"
          value={formatNumber(dataset.rows)}
          icon={Database}
          color="blue"
          subtitle="Uploaded rows"
        />

        <MetricCard
          title="Completeness"
          value={`${completeness.toFixed(2)}%`}
          icon={ShieldCheck}
          color="green"
          subtitle="Populated cells"
        />

        <MetricCard
          title="Missing Values"
          value={formatNumber(totalMissing)}
          icon={AlertCircle}
          color="orange"
          subtitle="Empty cells"
        />

        <MetricCard
          title="Duplicate Rows"
          value={formatNumber(duplicateCount)}
          icon={FileSpreadsheet}
          color="purple"
          subtitle="Duplicate records"
        />
      </div>

      <div className="panel quality-progress-panel">
        <div className="panel-heading">
          <div>
            <h3>Dataset Completeness</h3>
            <p>Percentage of cells containing values</p>
          </div>
          <strong>{completeness.toFixed(2)}%</strong>
        </div>

        <div className="quality-progress-track">
          <div
            className="quality-progress-fill"
            style={{ width: `${completeness}%` }}
          />
        </div>

        <small>
          {Math.max(0, totalCells - totalMissing)} of {totalCells} cells are populated.
        </small>
      </div>

      {pipelineResult && <PipelineSummary result={pipelineResult} />}

      <div className="panel quality-chart-panel">
        <div className="panel-heading">
          <div>
            <h3>Missing Values by Column</h3>
            <p>Empty cells in each column</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid stroke="#273044" strokeDasharray="3 3" />
            <XAxis dataKey="column" stroke="#8b95a9" />
            <YAxis allowDecimals={false} stroke="#8b95a9" />
            <Tooltip />
            <Bar dataKey="missing" fill="#f59e0b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="panel quality-table-panel">
        <div className="panel-heading">
          <div>
            <h3>Column Quality Details</h3>
            <p>Missing value status for each column</p>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Missing Values</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {Object.entries(missingValues).map(([column, count]) => (
                <tr key={column}>
                  <td>{column}</td>
                  <td>{formatNumber(count)}</td>
                  <td>
                    {Number(count) > 0
                      ? <span className="quality-cell-warning">Needs Review</span>
                      : <span className="quality-cell-good">Complete</span>}
                  </td>
                </tr>
              ))}

              {Object.keys(missingValues).length === 0 && (
                <tr>
                  <td colSpan="3">No column quality information available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className={`quality-alert ${hasIssues ? "warning" : "good"}`}>
        {hasIssues ? <AlertTriangle size={20} /> : <CheckCircle size={20} />}

        <div>
          <strong>
            {hasIssues ? "Data Quality Issues Found" : "Dataset Passed These Checks"}
          </strong>
          <p>
            {totalMissing} missing values and {duplicateCount} duplicate rows detected.
          </p>
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------
// DATA EXPLORER
// --------------------------------------------------

function DataExplorer({ dataset }) {
  if (!dataset) {
    return (
      <EmptyPage
        title="Data Explorer"
        message="Upload a CSV dataset to explore its records."
      />
    );
  }

  const columns = dataset.column_names || [];

  return (
    <div className="dashboard-content">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h3>Dataset Explorer</h3>
            <p>
              {dataset.filename} · {dataset.rows} records · {dataset.columns} columns
            </p>
          </div>
          <Eye size={24} />
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map(column => <th key={column}>{column}</th>)}
              </tr>
            </thead>

            <tbody>
              {(dataset.preview || []).map((row, index) => (
                <tr key={index}>
                  {columns.map(column => (
                    <td key={column}>{String(row?.[column] ?? "—") || "—"}</td>
                  ))}
                </tr>
              ))}

              {(!dataset.preview || dataset.preview.length === 0) && (
                <tr>
                  <td colSpan={Math.max(columns.length, 1)}>
                    No preview records available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <small>Showing the preview records returned by the upload API.</small>
      </div>
    </div>
  );
}

// --------------------------------------------------
// PIPELINE RUNS
// --------------------------------------------------

function PipelineRuns({ history = [], loading, error, onRefresh }) {
  const [selectedRun, setSelectedRun] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const viewDetails = async runId => {
    if (!runId) {
      setDetailsError("Pipeline run ID is missing.");
      return;
    }

    setDetailsLoading(true);
    setDetailsError("");
    setSelectedRun(null);

    try {
      const response = await getPipelineRunDetails(runId);

      const details =
        response?.run ??
        response?.history ??
        response?.data?.run ??
        response?.data ??
        response;

      setSelectedRun(normalizeRun(details));
    } catch (err) {
      setDetailsError(
        getErrorMessage(err, "Unable to load pipeline run details.")
      );
    } finally {
      setDetailsLoading(false);
    }
  };

  return (
    <div className="dashboard-content">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h3>Pipeline Run History</h3>
            <p>Saved pipeline executions from the database.</p>
          </div>

          <button
            className="upload-action-btn"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw size={17} />
            {loading ? "Refreshing..." : "Refresh History"}
          </button>
        </div>

        <ErrorMessage>{error}</ErrorMessage>

        {loading ? (
          <LoadingMessage message="Loading pipeline history..." />
        ) : history.length === 0 ? (
          <div className="quality-empty">
            <GitBranch size={38} />
            <h3>No Pipeline Runs Yet</h3>
            <p>
              Upload a CSV dataset and run the pipeline
              to see execution history here.
            </p>
          </div>
        ) : (
          <>
            <div className="upload-stats">
              <div className="upload-stat">
                <span>Total Pipeline Runs</span>
                <strong>{history.length}</strong>
              </div>

              <div className="upload-stat">
                <span>Latest Dataset</span>
                <strong>{history[0]?.filename || "—"}</strong>
              </div>

              <div className="upload-stat">
                <span>Latest Quality Score</span>
                <strong>{Number(history[0]?.quality_score || 0).toFixed(2)}%</strong>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Dataset</th>
                    <th>Execution Date</th>
                    <th>Quality Score</th>
                    <th>Total</th>
                    <th>Valid</th>
                    <th>Rejected</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {history.map((rawRun, index) => {
                    const run = normalizeRun(rawRun);

                    return (
                      <tr key={run.run_id || index}>
                        <td>{String(run.run_id).slice(0, 12)}</td>
                        <td>{run.filename}</td>
                        <td>{formatDate(run.executed_at)}</td>
                        <td>{run.quality_score.toFixed(2)}%</td>
                        <td>{formatNumber(run.total_records)}</td>
                        <td>{formatNumber(run.valid_records)}</td>
                        <td>{formatNumber(run.rejected_records)}</td>
                        <td>
                          <span className={`quality-status ${
                            isCompleted(run.status) ? "good" : "warning"
                          }`}>
                            {run.status}
                          </span>
                        </td>
                        <td>
                          <button
                            className="upload-action-btn"
                            onClick={() => viewDetails(run.run_id)}
                          >
                            <Eye size={16} /> View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {detailsLoading && <LoadingMessage message="Loading run details..." />}
      <ErrorMessage>{detailsError}</ErrorMessage>

      {selectedRun && (
        <div className="panel pipeline-summary">
          <div className="panel-heading">
            <div>
              <h3><Eye size={19} /> Pipeline Run Details</h3>
              <p>{selectedRun.filename}</p>
            </div>

            <span className={`quality-status ${
              isCompleted(selectedRun.status) ? "good" : "warning"
            }`}>
              {selectedRun.status}
            </span>
          </div>

          <div className="quality-stats-grid">
            <MetricCard
              title="Quality Score"
              value={`${selectedRun.quality_score.toFixed(2)}%`}
              icon={ShieldCheck}
              color="green"
              subtitle="Execution score"
            />

            <MetricCard
              title="Total Records"
              value={formatNumber(selectedRun.total_records)}
              icon={Database}
              color="blue"
              subtitle="Processed records"
            />

            <MetricCard
              title="Valid Records"
              value={formatNumber(selectedRun.valid_records)}
              icon={CheckCircle}
              color="green"
              subtitle="Accepted records"
            />

            <MetricCard
              title="Rejected Records"
              value={formatNumber(selectedRun.rejected_records)}
              icon={AlertTriangle}
              color="orange"
              subtitle="Rejected records"
            />
          </div>

          <div className="upload-stats">
            <div className="upload-stat">
              <span>Missing Value Rows</span>
              <strong>{formatNumber(selectedRun.missing_value_records)}</strong>
            </div>

            <div className="upload-stat">
              <span>Duplicate Rows</span>
              <strong>{formatNumber(selectedRun.duplicate_records)}</strong>
            </div>

            <div className="upload-stat">
              <span>Execution Date</span>
              <strong>{formatDate(selectedRun.executed_at)}</strong>
            </div>
          </div>

          <div className="report-downloads">
            <button
              className="upload-action-btn"
              onClick={() => downloadReport(selectedRun.run_id, "valid")}
            >
              <Download size={18} /> Download Valid CSV
            </button>

            <button
              className="upload-action-btn secondary-action"
              onClick={() => downloadReport(selectedRun.run_id, "rejected")}
            >
              <Download size={18} /> Download Rejected CSV
            </button>
          </div>

          <h3>Rejected Records Preview</h3>
          <RejectedPreview rows={selectedRun.rejected_preview || []} />
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------
// ALERTS
// --------------------------------------------------

function AlertsPage({ dataset, pipelineResult }) {
  const alerts = [];

  if (dataset) {
    Object.entries(dataset.missing_values || {}).forEach(([column, count]) => {
      if (Number(count) > 0) {
        alerts.push({
          title: `Missing values in ${column}`,
          detail: `${count} empty cells detected in this column.`
        });
      }
    });

    if (Number(dataset.duplicate_rows) > 0) {
      alerts.push({
        title: "Duplicate records detected",
        detail: `${dataset.duplicate_rows} duplicate rows found.`
      });
    }
  }

  if (pipelineResult) {
    const rejected = getTotal(
      pipelineResult,
      "rejected_rows",
      "rejected_records"
    );

    if (rejected > 0) {
      alerts.push({
        title: "Pipeline rejected records",
        detail: `${rejected} records were rejected.`
      });
    }
  }

  return (
    <div className="dashboard-content">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h3>Data Quality Alerts</h3>
            <p>Issues detected in the latest dataset and pipeline.</p>
          </div>
          <Bell size={24} />
        </div>

        {alerts.length === 0 ? (
          <div className="quality-empty">
            <CheckCircle size={38} />
            <h3>No Active Alerts</h3>
            <p>No data quality alerts are currently detected.</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div className="quality-alert warning" key={index}>
              <AlertTriangle size={20} />
              <div>
                <strong>{alert.title}</strong>
                <p>{alert.detail}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------
// REPORTS
// --------------------------------------------------

function ReportsPage({ pipelineResult, history = [] }) {
  const reports = useMemo(() => {
    if (history.length > 0) return history;
    return pipelineResult ? [normalizeRun(pipelineResult)] : [];
  }, [history, pipelineResult]);

  if (reports.length === 0) {
    return (
      <EmptyPage
        title="Reports"
        message="Run a pipeline to generate downloadable CSV reports."
      />
    );
  }

  return (
    <div className="dashboard-content">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h3>Generated Reports</h3>
            <p>Download output files from your pipeline runs.</p>
          </div>
          <FileText size={24} />
        </div>

        {reports.map((report, index) => (
          <div className="upload-stats" key={report.run_id || index}>
            <div className="upload-stat">
              <span>Dataset</span>
              <strong>{report.filename}</strong>
            </div>

            <div className="upload-stat">
              <span>Quality Score</span>
              <strong>{Number(report.quality_score || 0).toFixed(2)}%</strong>
            </div>

            <div className="upload-stat">
              <span>Run Date</span>
              <strong>{formatDate(report.executed_at)}</strong>
            </div>

            <div className="report-downloads">
              <button
                className="upload-action-btn"
                onClick={() => downloadReport(report.run_id, "valid")}
                disabled={!report.run_id}
              >
                <Download size={18} /> Download Valid Records
              </button>

              <button
                className="upload-action-btn secondary-action"
                onClick={() => downloadReport(report.run_id, "rejected")}
                disabled={!report.run_id}
              >
                <Download size={18} /> Download Rejected Records
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --------------------------------------------------
// OVERVIEW
// --------------------------------------------------

function Overview({ user, dataset, pipelineResult, history = [], onNavigate }) {
  const stats = [
    [
      "Total Records",
      dataset
        ? formatNumber(dataset.rows)
        : pipelineResult
          ? formatNumber(getTotal(pipelineResult, "total_rows", "total_records"))
          : "—",
      Database,
      "blue",
      "Latest uploaded dataset"
    ],
    [
      "Quality Score",
      pipelineResult
        ? `${Number(pipelineResult.quality_score || 0).toFixed(2)}%`
        : "—",
      ShieldCheck,
      "green",
      "Latest pipeline score"
    ],
    [
      "Valid Records",
      pipelineResult
        ? formatNumber(getTotal(pipelineResult, "valid_rows", "valid_records"))
        : "—",
      CheckCircle,
      "purple",
      "Accepted records"
    ],
    [
      "Rejected Records",
      pipelineResult
        ? formatNumber(getTotal(pipelineResult, "rejected_rows", "rejected_records"))
        : "—",
      AlertTriangle,
      "orange",
      "Records requiring review"
    ]
  ];

  const completedRuns = history.filter(run => isCompleted(run.status));

  const trendData = completedRuns
    .slice(0, 7)
    .reverse()
    .map((run, index) => ({
      day: run.executed_at
        ? new Date(run.executed_at).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric"
          })
        : `Run ${index + 1}`,
      quality: Number(run.quality_score || 0)
    }));

  const hasRealTrend = trendData.length > 0;

  const volumeData = dataset
    ? [
        { name: "Total", records: Number(dataset.rows || 0) },
        { name: "Columns", records: Number(dataset.columns || 0) },
        {
          name: "Missing",
          records: Object.values(dataset.missing_values || {})
            .reduce((sum, value) => sum + Number(value || 0), 0)
        },
        { name: "Duplicates", records: Number(dataset.duplicate_rows || 0) }
      ]
    : [];

  return (
    <div className="dashboard-content">
      <div className="welcome-section">
        <div>
          <h1>Welcome back, {user.username} 👋</h1>
          <p>Here's what's happening with your data today.</p>
        </div>

        <span className="demo-label">
          {dataset || pipelineResult ? "LIVE DATA" : "AWAITING DATA"}
        </span>
      </div>

      <div className="stats-grid">
        {stats.map(([title, value, Icon, color, subtitle]) => (
          <div className="stat-card" key={title}>
            <div className={`stat-icon ${color}`}>
              <Icon size={22} />
            </div>
            <p>{title}</p>
            <h2>{value}</h2>
            <small>{subtitle}</small>
          </div>
        ))}
      </div>

      {!dataset && !pipelineResult && (
        <div className="panel">
          <h3>Get started with data quality monitoring</h3>
          <p>Upload your CSV dataset to start validating records.</p>

          <button
            className="upload-action-btn"
            onClick={() => onNavigate("Upload Data")}
          >
            <Upload size={18} /> Upload Dataset
          </button>
        </div>
      )}

      <div className="charts-grid">
        <div className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Data Quality Trend</h3>
              <p>
                {hasRealTrend
                  ? "Quality score from recent pipeline runs"
                  : "No pipeline history available yet"}
              </p>
            </div>
            <span className="chart-tag">
              {hasRealTrend ? "LIVE HISTORY" : "NO DATA"}
            </span>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="qualityFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>

              <CartesianGrid stroke="#273044" strokeDasharray="3 3" />
              <XAxis dataKey="day" stroke="#8b95a9" />
              <YAxis domain={[0, 100]} stroke="#8b95a9" />
              <Tooltip />

              <Area
                type="monotone"
                dataKey="quality"
                stroke="#9b7bff"
                fill="url(#qualityFill)"
                strokeWidth={3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Dataset Distribution</h3>
              <p>
                {dataset
                  ? "Statistics from the uploaded dataset"
                  : "Upload a dataset to display statistics"}
              </p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={volumeData}>
              <CartesianGrid stroke="#273044" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#8b95a9" />
              <YAxis allowDecimals={false} stroke="#8b95a9" />
              <Tooltip />

              <Bar dataKey="records" fill="#7c5cff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel activity-panel">
        <div className="panel-heading">
          <div>
            <h3>Platform Modules</h3>
            <p>Navigate to monitoring features</p>
          </div>
        </div>

        <div className="module-grid">
          {[
            ["Data Ingestion", "Upload and ingest CSV datasets", Upload, "Upload Data"],
            ["Pipeline Monitoring", "Track execution and run history", GitBranch, "Pipeline Runs"],
            ["Baseline Comparison", "Compare current and previous runs", GitCompareArrows, "Baseline Comparison"],
            ["Quality Validation", "Detect missing and invalid values", ShieldCheck, "Data Quality"],
            ["Alert Management", "Review data quality issues", Bell, "Alerts"]
          ].map(([title, description, Icon, page]) => (
            <button
              className="module-card"
              key={title}
              onClick={() => onNavigate(page)}
            >
              <Icon size={22} />
              <div>
                <strong>{title}</strong>
                <p>{description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------
// MAIN DASHBOARD
// --------------------------------------------------

function Dashboard({ user, onLogout }) {
  const [activePage, setActivePage] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [dataset, setDataset] = useState(null);
  const [pipelineHistory, setPipelineHistory] = useState([]);

  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");

  const pipelineResult = pipelineHistory.length > 0
    ? pipelineHistory[0]
    : null;

  const navigate = page => {
    setActivePage(page);
    setSidebarOpen(false);
  };

  const loadPipelineHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await getPipelineHistory();
      const rows = extractHistory(response);

      // API is expected to return newest-first. Sort defensively by date.
      rows.sort((a, b) => {
        const dateA = new Date(a.executed_at || 0).getTime();
        const dateB = new Date(b.executed_at || 0).getTime();

        return dateB - dateA;
      });

      setPipelineHistory(rows);
    } catch (error) {
      setHistoryError(
        getErrorMessage(error, "Unable to load pipeline history.")
      );
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPipelineHistory();
  }, [loadPipelineHistory]);

  // Refresh history after every successful API response.
  // Do not depend on one exact capitalization of the status field.
  const handlePipelineSuccess = async result => {
    if (!result) return;

    await loadPipelineHistory();

    // If the API returns a successful run but history refresh has not
    // included it yet, retain the response temporarily in the UI.
    const newRun = normalizeRun(result);

    if (newRun.run_id) {
      setPipelineHistory(previous => {
        const alreadyExists = previous.some(
          run => run.run_id === newRun.run_id
        );

        if (alreadyExists) return previous;

        return [newRun, ...previous];
      });
    }
  };

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck />
          </div>

          <div>
            <h2>YottaFlex<span>.ai</span></h2>
            <small>DATA INTELLIGENCE</small>
          </div>

          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
          >
            <X />
          </button>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav>
          {navItems.map(item => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${activePage === item.name ? "active" : ""}`}
                onClick={() => navigate(item.name)}
              >
                <Icon size={19} />
                <span>{item.name}</span>

                {item.name === "Baseline Comparison" && (
                  <small>
                    {pipelineHistory.filter(run => isCompleted(run.status)).length}/2
                  </small>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => navigate("Overview")}>
            <Settings size={19} />
            <span>Settings</span>
          </button>

          <div className="user-profile">
            <div className="avatar">
              {user.username?.[0]?.toUpperCase() || "U"}
            </div>

            <div className="user-info">
              <strong>{user.username}</strong>
              <small>{user.role}</small>
            </div>

            <button className="logout-btn" onClick={onLogout}>
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button
            className="menu-btn"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu />
          </button>

          <div>
            <h2>{activePage}</h2>
            <p>Monitor, analyze and manage your data quality</p>
          </div>

          <div className="topbar-right">
            <span className="system-status">
              <span className="status-dot" />
              System Online
            </span>

            <div className="top-avatar">
              {user.username?.[0]?.toUpperCase() || "U"}
            </div>
          </div>
        </header>

        {activePage === "Overview" && (
          <Overview
            user={user}
            dataset={dataset}
            pipelineResult={pipelineResult}
            history={pipelineHistory}
            onNavigate={navigate}
          />
        )}

        {activePage === "Upload Data" && (
          <UploadData
            dataset={dataset}
            pipelineResult={pipelineResult}
            onUploadSuccess={setDataset}
            onPipelineSuccess={handlePipelineSuccess}
          />
        )}

        {activePage === "Data Explorer" && (
          <DataExplorer dataset={dataset} />
        )}

        {activePage === "Pipeline Runs" && (
          <PipelineRuns
            history={pipelineHistory}
            loading={historyLoading}
            error={historyError}
            onRefresh={loadPipelineHistory}
          />
        )}

        {activePage === "Baseline Comparison" && (
          <BaselineComparison history={pipelineHistory} />
        )}

        {activePage === "Data Quality" && (
          <DataQuality
            dataset={dataset}
            pipelineResult={pipelineResult}
          />
        )}

        {activePage === "Alerts" && (
          <AlertsPage
            dataset={dataset}
            pipelineResult={pipelineResult}
          />
        )}

        {activePage === "Reports" && (
          <ReportsPage
            pipelineResult={pipelineResult}
            history={pipelineHistory}
          />
        )}
      </main>
    </div>
  );
}

// --------------------------------------------------
// APP AUTHENTICATION
// --------------------------------------------------

export default function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("yotta_user");
      const token = localStorage.getItem("yotta_token");

      if (savedUser && token) {
        setUser(JSON.parse(savedUser));
      }
    } catch {
      localStorage.removeItem("yotta_user");
      localStorage.removeItem("yotta_token");
    } finally {
      setCheckingAuth(false);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("yotta_token");
    localStorage.removeItem("yotta_user");
    setUser(null);
  };

  if (checkingAuth) {
    return (
      <div className="loading-screen">
        Loading YottaFlex.ai...
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <Dashboard
      user={user}
      onLogout={handleLogout}
    />
  );
}
