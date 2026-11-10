"use client";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Bell,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Database,
  FileClock,
  Gauge,
  LayoutDashboard,
  MoreHorizontal,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Trash2,
  Workflow,
  XCircle,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  activity,
  executions,
  logs,
  pipelines,
  qualityIssues,
  sources,
  refreshData,
  type Status,
} from "@/lib/api";

const nav = [
  ["Overview", LayoutDashboard],
  ["Pipelines", Workflow],
  ["Data sources", Database],
  ["Data quality", ShieldCheck],
  ["Execution history", FileClock],
  ["Logs & errors", AlertCircle],
] as const;
const trend = [
  { day: "Oct 25", runs: 182, failures: 4 },
  { day: "Oct 26", runs: 214, failures: 3 },
  { day: "Oct 27", runs: 198, failures: 6 },
  { day: "Oct 28", runs: 240, failures: 2 },
  { day: "Oct 29", runs: 226, failures: 5 },
  { day: "Oct 30", runs: 244, failures: 3 },
  { day: "Oct 31", runs: 280, failures: 4 },
];
function Badge({ status }: { status: string }) {
  return (
    <span className={`badge ${status.toLowerCase()}`}>
      <span className="badge-dot" />
      {status}
    </span>
  );
}
function Shell({
  active,
  setActive,
  children,
}: {
  active: string;
  setActive: (x: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <Zap size={17} fill="currentColor" />
          </span>
          RetailFlow
        </div>
        <div className="nav-section">Workspace</div>
        {nav.map(([label, Icon]) => {
          const NavIcon = Icon;
          return (
            <button
              key={label}
              onClick={() => setActive(label)}
              className={`nav-item ${active === label ? "active" : ""}`}
            >
              <NavIcon size={16} />
              {label}
            </button>
          );
        })}
        <div className="nav-section">Manage</div>
        <button className="nav-item">
          <Settings size={16} />
          Settings
        </button>
        <button className="nav-item">
          <CircleHelp size={16} />
          Help center
        </button>
        <div className="sidebar-bottom">
          <div className="user">
            <div className="avatar">MW</div>
            <div>
              <div className="user-name">Maya Wilson</div>
              <div className="user-role">Operations admin</div>
            </div>
            <ChevronDown size={14} style={{ marginLeft: "auto" }} />
          </div>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="crumb">
            Workspace <span>/</span> <strong>{active}</strong>
          </div>
          <div className="top-actions">
            <div className="status">
              <span className="dot" />
              All systems operational
            </div>
            <button className="icon-btn">
              <Bell size={16} />
            </button>
            <button className="icon-btn">
              <Search size={16} />
            </button>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
function Header({
  title,
  sub,
  action,
}: {
  title: string;
  sub: string;
  action?: string;
}) {
  return (
    <div className="page-title">
      <div>
        <p className="eyebrow">RetailFlow workspace</p>
        <h1>{title}</h1>
        <p>{sub}</p>
      </div>
      {action && (
        <button className="primary">
          <Plus size={15} />
          {action}
        </button>
      )}
    </div>
  );
}
function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <section className={`card ${className}`}>{children}</section>;
}
function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: React.ReactNode[][];
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Overview() {
  return (
    <>
      <Header
        title="Operations overview"
        sub="Monitor your data pipelines and platform health."
      />
      <div className="grid-kpi">
        {[
          ["Active pipelines", "24", Workflow, "+12.5%"],
          ["Successful executions", "1,284", CheckCircle2, "+8.2%"],
          ["Failed executions", "37", XCircle, "-4.6%"],
          ["Records processed", "2.4M", Database, "+18.9%"],
          ["Data quality score", "98.6%", Gauge, "+1.2%"],
        ].map((item) => {
          const [label, value, Icon, trend] = item as [
            string,
            string,
            typeof Workflow,
            string,
          ];
          const KpiIcon = Icon;
          return (
            <Card className="kpi" key={String(label)}>
              <div className="kpi-top">
                <span>{label}</span>
                <span className="kpi-icon">
                  <KpiIcon size={16} />
                </span>
              </div>
              <div className="kpi-value">{value}</div>
              <div
                className={`trend ${String(trend).startsWith("-") ? "bad" : ""}`}
              >
                {trend} <span>vs. last 30 days</span>
              </div>
            </Card>
          );
        })}
      </div>
      <div className="content-grid">
        <Card className="chart-card">
          <div className="card-head">
            <div>
              <div className="card-title">Pipeline execution trends</div>
              <div className="card-sub">
                Successful runs and failures over the last 7 days
              </div>
            </div>
            <button className="date-chip">
              Last 7 days <ChevronDown size={12} />
            </button>
          </div>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#edf0f4"
                />
                <XAxis
                  dataKey="day"
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                />
                <YAxis tickLine={false} axisLine={false} fontSize={11} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="runs"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="failures"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <div className="card-head">
            <div>
              <div className="card-title">Data quality overview</div>
              <div className="card-sub">Across all active sources</div>
            </div>
            <Gauge size={18} color="#2563eb" />
          </div>
          <div className="quality-ring">
            <div>
              <strong>98.6</strong>
              <small>%</small>
              <span>Excellent</span>
            </div>
          </div>
          <div className="quality-stats">
            <span>
              <b>242,450</b> Valid records
            </span>
            <span>
              <b>3,440</b> Invalid records
            </span>
          </div>
        </Card>
      </div>
      <div className="split-grid">
        <Card>
          <div className="card-head">
            <div>
              <div className="card-title">Recent executions</div>
              <div className="card-sub">Latest pipeline activity</div>
            </div>
            <button className="link-btn">View all</button>
          </div>
          <Table
            headers={["Pipeline", "Status", "Records", "Duration"]}
            rows={executions
              .slice(0, 5)
              .map((e) => [
                <b>{e.pipeline}</b>,
                <Badge status={e.status} />,
                e.records,
                e.duration,
              ])}
          />
        </Card>
        <Card>
          <div className="card-head">
            <div>
              <div className="card-title">System activity</div>
              <div className="card-sub">Recent events and alerts</div>
            </div>
            <Activity size={17} color="#2563eb" />
          </div>
          <div className="activity-list">
            {activity.map((a, i) => (
              <div className="activity-row" key={a}>
                <span className={`activity-icon ${i === 1 ? "danger" : ""}`}>
                  {i === 1 ? (
                    <AlertCircle size={14} />
                  ) : (
                    <CheckCircle2 size={14} />
                  )}
                </span>
                <span>
                  {a}
                  <small>
                    Today, {10 + i}:2{i} AM
                  </small>
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  );
}
function DataSources() {
  const [q, setQ] = useState("");
  const filtered = sources.filter((s) =>
    s.name.toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <>
      <Header
        title="Data sources"
        sub="Connect and monitor the systems powering your data operations."
        action="Add data source"
      />
      <Card>
        <div className="toolbar">
          <div className="search">
            <Search size={15} />
            <input
              placeholder="Search data sources"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button className="filter">
            All types <ChevronDown size={13} />
          </button>
          <button className="filter">
            All statuses <ChevronDown size={13} />
          </button>
        </div>
        <Table
          headers={[
            "Source",
            "Type",
            "Status",
            "Last sync",
            "Records imported",
            "Created",
            "",
          ]}
          rows={filtered.map((s) => [
            <div className="table-primary">
              <span className="source-icon">
                <Database size={15} />
              </span>
              <b>{s.name}</b>
            </div>,
            s.type,
            <Badge status={s.status} />,
            s.sync,
            s.records,
            s.created,
            <button className="more">
              <MoreHorizontal size={17} />
            </button>,
          ])}
        />
        <div className="table-footer">
          Showing {filtered.length} of 8 data sources{" "}
          <span>
            1 2 <b>Next →</b>
          </span>
        </div>
      </Card>
    </>
  );
}

function Pipelines() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState(pipelines);
  useEffect(() => {
    setItems(pipelines);
  }, [pipelines]);
  const filtered = items.filter((p) =>
    p.name.toLowerCase().includes(q.toLowerCase()),
  );
  const run = (name: string) =>
    setItems(
      items.map((p) => (p.name === name ? { ...p, status: "Running" } : p)),
    );
  return (
    <>
      <Header
        title="Pipelines"
        sub="Build, run, and monitor your ETL workflows."
        action="Create pipeline"
      />
      <Card>
        <div className="toolbar">
          <div className="search">
            <Search size={15} />
            <input
              placeholder="Search pipelines"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button className="filter">
            All statuses <ChevronDown size={13} />
          </button>
          <button className="filter">
            Sort: Recent <ChevronDown size={13} />
          </button>
        </div>
        <Table
          headers={[
            "Pipeline",
            "Source → Destination",
            "Status",
            "Last duration",
            "Records",
            "Success rate",
            "",
          ]}
          rows={filtered.map((p) => [
            <b>{p.name}</b>,
            <span className="muted">
              {p.source} <span>→</span> {p.destination}
            </span>,
            <Badge status={p.status} />,
            p.duration,
            p.records,
            <span className="success-rate">{p.rate}</span>,
            <button className="run-btn" onClick={() => run(p.name)}>
              {p.status === "Running" ? (
                <Pause size={14} />
              ) : (
                <Play size={14} />
              )}
            </button>,
          ])}
        />
        <div className="table-footer">
          Showing {filtered.length} of 10 pipelines{" "}
          <span>
            1 2 3 <b>Next →</b>
          </span>
        </div>
      </Card>
    </>
  );
}

function Quality() {
  const [q, setQ] = useState("");
  const [issues, setIssues] = useState(qualityIssues);
  useEffect(() => {
    setIssues(qualityIssues);
  }, [qualityIssues]);
  const filtered = issues.filter((i) =>
    i.error.toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <>
      <Header
        title="Data quality"
        sub="Monitor validation rules and resolve issues before they impact reporting."
      />
      <div className="grid-kpi">
        {[
          ["Overall quality", "98.6%"],
          ["Records validated", "245,890"],
          ["Valid records", "242,450"],
          ["Invalid records", "3,440"],
          ["Validation rules", "18"],
          ["Failed rules", "3"],
        ].map(([l, v]) => (
          <Card className="kpi compact" key={l}>
            <span>{l}</span>
            <div className="kpi-value">{v}</div>
          </Card>
        ))}
      </div>
      <div className="split-grid">
        <Card>
          <div className="card-head">
            <div>
              <div className="card-title">Quality score trend</div>
              <div className="card-sub">Daily validation performance</div>
            </div>
          </div>
          <div className="chart-box small">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#edf0f4"
                />
                <XAxis
                  dataKey="day"
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                />
                <Bar dataKey="runs" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <div className="card-title">Validation rules overview</div>
          <div className="rule-list">
            <span>
              Required fields <b>8 / 8 passing</b>
            </span>
            <span>
              Format validation <b>5 / 6 passing</b>
            </span>
            <span>
              Uniqueness checks <b>2 / 4 passing</b>
            </span>
            <span>
              Range validation <b>3 / 3 passing</b>
            </span>
          </div>
        </Card>
      </div>
      <Card>
        <div className="toolbar">
          <div className="search">
            <Search size={15} />
            <input
              placeholder="Search validation issues"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button className="filter">
            All severity <ChevronDown size={13} />
          </button>
          <button className="filter">
            All datasets <ChevronDown size={13} />
          </button>
          <button
            className="secondary"
            onClick={() =>
              setIssues(issues.map((i) => ({ ...i, status: "Open" })))
            }
          >
            <RefreshCw size={14} /> Re-run validation
          </button>
        </div>
        <Table
          headers={[
            "Record ID",
            "Dataset",
            "Field",
            "Validation rule",
            "Issue",
            "Severity",
            "Status",
          ]}
          rows={filtered.map((i) => [
            <b>{i.id}</b>,
            i.dataset,
            i.field,
            i.rule,
            <span className="issue">{i.error}</span>,
            <Badge status={i.severity} />,
            <button
              className="status-link"
              onClick={() =>
                setIssues(
                  issues.map((x) =>
                    x.id === i.id ? { ...x, status: "Resolved" } : x,
                  ),
                )
              }
            >
              {i.status}
            </button>,
          ])}
        />
      </Card>
    </>
  );
}
function History() {
  const [q, setQ] = useState("");
  const filtered = executions.filter((e) =>
    e.pipeline.toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <>
      <Header
        title="Execution history"
        sub="Trace every pipeline run with detailed records and logs."
      />
      <Card>
        <div className="toolbar">
          <div className="search">
            <Search size={15} />
            <input
              placeholder="Search executions"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button className="filter">
            All statuses <ChevronDown size={13} />
          </button>
          <button className="filter">
            All pipelines <ChevronDown size={13} />
          </button>
          <button className="filter">
            Date range <ChevronDown size={13} />
          </button>
        </div>
        <Table
          headers={[
            "Execution ID",
            "Pipeline",
            "Status",
            "Started",
            "Duration",
            "Records",
            "Trigger",
            "",
          ]}
          rows={filtered.map((e) => [
            <b>{e.id}</b>,
            e.pipeline,
            <Badge status={e.status} />,
            e.start,
            e.duration,
            e.records,
            <span className="muted">{e.trigger}</span>,
            <button className="more">
              <MoreHorizontal size={17} />
            </button>,
          ])}
        />
        <div className="table-footer">
          Showing {filtered.length} executions{" "}
          <span>
            ← Prev &nbsp; <b>1</b> &nbsp; 2 &nbsp; 3 &nbsp; Next →
          </span>
        </div>
      </Card>
    </>
  );
}
function Logs() {
  const [q, setQ] = useState("");
  const [level, setLevel] = useState("All");
  const filtered = logs.filter(
    (l) =>
      (level === "All" || l.level === level) &&
      l.message.toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <>
      <Header
        title="Logs & errors"
        sub="Centralized visibility into every pipeline event and system signal."
      />
      <Card>
        <div className="toolbar">
          <div className="search">
            <Search size={15} />
            <input
              placeholder="Search logs and messages"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div className="segmented">
            {["All", "INFO", "WARNING", "ERROR", "DEBUG"].map((x) => (
              <button
                className={level === x ? "selected" : ""}
                onClick={() => setLevel(x)}
                key={x}
              >
                {x}
              </button>
            ))}
          </div>
          <button className="filter">
            Today <ChevronDown size={13} />
          </button>
        </div>
        <div className="log-list">
          {filtered.map((l) => (
            <div className={`log-row ${l.level.toLowerCase()}`} key={l.id}>
              <span className="log-time">{l.time}</span>
              <b className="log-level">{l.level}</b>
              <span className="log-pipeline">{l.pipeline}</span>
              <span className="log-message">{l.message}</span>
              <span className="muted">{l.component}</span>
              <button className="more">
                <MoreHorizontal size={16} />
              </button>
            </div>
          ))}
        </div>
        <div className="table-footer">
          Showing {filtered.length} of 24 log entries
        </div>
      </Card>
    </>
  );
}

function App() {
  const [active, setActive] = useState("Overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshData()
      .catch((err) => {
        console.error("Failed to load RetailFlow data:", err);
        setError(err.message || "Unable to connect to the backend.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const page =
    active === "Overview" ? (
      <Overview />
    ) : active === "Data sources" ? (
      <DataSources />
    ) : active === "Pipelines" ? (
      <Pipelines />
    ) : active === "Data quality" ? (
      <Quality />
    ) : active === "Execution history" ? (
      <History />
    ) : (
      <Logs />
    );

  return (
    <Shell active={active} setActive={setActive}>
      {loading && <p>Loading RetailFlow data...</p>}

      {error && (
        <div style={{ color: "red", padding: "12px" }}>
          Backend connection error: {error}
        </div>
      )}

      {!loading && !error && page}
    </Shell>
  );
}

export default App;
