
import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const STATUSES = [
  "Submitted",
  "In Progress",
  "Resolved",
  "Rejected",
];

const emptyForm = {
  title: "",
  category: "Infrastructure",
  location: "",
  description: "",
};

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function App() {
  const [complaints, setComplaints] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);

  const loadComplaints = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/complaints`);

      if (!response.ok) {
        throw new Error("Could not load complaints from the server.");
      }

      const data = await response.json();
      setComplaints(data);
    } catch {
      setError(
        "Unable to connect to SmartCampus. Check that the FastAPI server is running."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadComplaints();
  }, [loadComplaints]);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  };

  const submitComplaint = async (event) => {
    event.preventDefault();
    setNotice("");
    setError("");
    setSubmitting(true);

    try {
      const description = form.location.trim()
        ? `Location: ${form.location.trim()}\n\n${form.description.trim()}`
        : form.description.trim();

      const response = await fetch(`${API_URL}/api/complaints`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: form.title.trim(),
          description,
          category: form.category,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "The complaint could not be submitted."
        );
      }

      setForm(emptyForm);
      setShowForm(false);
      setNotice(`Complaint ${result.ticket_id} submitted successfully!`);

      await loadComplaints();
    } catch (err) {
      setError(
        err.message ||
          "Could not submit the complaint. Check your backend connection."
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Update complaint status using the FastAPI PATCH endpoint.
  const updateComplaintStatus = async (complaintId, newStatus) => {
    setNotice("");
    setError("");
    setUpdatingId(complaintId);

    try {
      const response = await fetch(
        `${API_URL}/api/complaints/${complaintId}/status`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status: newStatus }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Could not update the complaint status."
        );
      }

      setNotice(
        `${result.ticket_id}: status changed to ${result.status}.`
      );

      await loadComplaints();
    } catch (err) {
      setError(
        err.message ||
          "Could not update the status. Check your backend connection."
      );
    } finally {
      setUpdatingId(null);
    }
  };

  const visibleComplaints = complaints.filter((complaint) =>
    [
      complaint.ticket_id,
      complaint.title,
      complaint.category,
      complaint.department,
      complaint.status,
    ]
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const stats = [
    {
      label: "Total Complaints",
      value: complaints.length,
      icon: "▤",
      color: "blue",
    },
    {
      label: "Pending",
      value: complaints.filter((c) => c.status === "Submitted").length,
      icon: "◷",
      color: "orange",
    },
    {
      label: "In Progress",
      value: complaints.filter((c) => c.status === "In Progress").length,
      icon: "↻",
      color: "purple",
    },
    {
      label: "Resolved",
      value: complaints.filter((c) => c.status === "Resolved").length,
      icon: "✓",
      color: "green",
    },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">SC</div>
          <div>
            <h2>SmartCampus</h2>
            <span>Grievance Portal</span>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>

        <button className="nav-item active" type="button">
          <span>▦</span> Dashboard
        </button>

        <button
          className="nav-item"
          type="button"
          onClick={() => {
            setNotice("");
            setError("");
            setShowForm(true);
          }}
        >
          <span>＋</span> Submit Complaint
        </button>

        <button
          className="nav-item"
          type="button"
          onClick={() =>
            document
              .getElementById("complaints")
              ?.scrollIntoView({ behavior: "smooth" })
          }
        >
          <span>▤</span> My Complaints
        </button>

        <div className="sidebar-bottom">
          <div className="help-card">
            <div className="help-icon">?</div>
            <strong>Need help?</strong>
            <p>
              Report an issue and we'll route it to the right department.
            </p>
            <button
              type="button"
              onClick={() => setShowForm(true)}
            >
              Report an issue →
            </button>
          </div>

          <div className="profile">
            <div className="avatar">S</div>
            <div>
              <strong>Campus User</strong>
              <span>Student account</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Dashboard
          </div>

          <div className="topbar-right">
            <span className="live-dot"></span>
            <span className="system-status">Campus services portal</span>
            <div className="avatar">S</div>
          </div>
        </header>

        <section className="page-content">
          <div className="welcome-row">
            <div>
              <p className="eyebrow">CAMPUS SUPPORT CENTER</p>
              <h1>
                Good morning! <span className="wave">✳</span>
              </h1>
              <p className="subtitle">
                Report issues, track progress, and help make your campus better.
              </p>
            </div>

            <button
              className="primary-button"
              type="button"
              onClick={() => {
                setNotice("");
                setError("");
                setShowForm(true);
              }}
            >
              <span>＋</span> New complaint
            </button>
          </div>

          {notice && (
            <div className="notice" role="status">
              <span>✓</span> {notice}
              <button type="button" onClick={() => setNotice("")}>
                ×
              </button>
            </div>
          )}

          {error && (
            <div className="notice" role="alert">
              <span>!</span> {error}
              <button type="button" onClick={() => setError("")}>
                ×
              </button>
            </div>
          )}

          <div className="stats-grid">
            {stats.map((stat) => (
              <div className="stat-card" key={stat.label}>
                <div className={`stat-icon ${stat.color}`}>
                  {stat.icon}
                </div>
                <div className="stat-label">{stat.label}</div>
                <div className="stat-value">
                  {loading ? "—" : stat.value}
                </div>
                <div className="stat-footnote">
                  Based on saved tickets
                </div>
              </div>
            ))}
          </div>

          <section className="panel quick-panel">
            <div>
              <div className="panel-icon">✦</div>
              <div>
                <h3>Have something that needs attention?</h3>
                <p>
                  Tell us what's happening. Your complaint will be routed to
                  the appropriate department.
                </p>
              </div>
            </div>

            <button
              className="secondary-button"
              type="button"
              onClick={() => setShowForm(true)}
            >
              Create a ticket <span>→</span>
            </button>
          </section>

          {showForm && (
            <section className="panel form-panel" id="new-complaint">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">NEW TICKET</p>
                  <h2>Submit a complaint</h2>
                  <p className="subtitle">
                    Provide accurate details so the right team can help.
                  </p>
                </div>

                <button
                  className="close-button"
                  type="button"
                  onClick={() => setShowForm(false)}
                  aria-label="Close form"
                >
                  ×
                </button>
              </div>

              <form onSubmit={submitComplaint}>
                <label>
                  Complaint title
                  <input
                    name="title"
                    value={form.title}
                    onChange={updateField}
                    placeholder="e.g. Wi-Fi not working in Block A"
                    required
                    minLength={3}
                    maxLength={200}
                  />
                </label>

                <div className="form-grid">
                  <label>
                    Category
                    <select
                      name="category"
                      value={form.category}
                      onChange={updateField}
                    >
                      <option>Infrastructure</option>
                      <option>Wi-Fi</option>
                      <option>Cleanliness</option>
                      <option>Transport</option>
                    </select>
                  </label>

                  <label>
                    Location
                    <input
                      name="location"
                      value={form.location}
                      onChange={updateField}
                      placeholder="e.g. Block A, Room 204"
                      required
                    />
                  </label>
                </div>

                <label>
                  Description
                  <textarea
                    name="description"
                    value={form.description}
                    onChange={updateField}
                    placeholder="Describe the issue and when you noticed it..."
                    rows={4}
                    required
                    minLength={5}
                    maxLength={2000}
                  />
                </label>

                <div className="form-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setShowForm(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </button>

                  <button
                    className="primary-button"
                    type="submit"
                    disabled={submitting}
                  >
                    {submitting ? "Submitting..." : "Submit complaint →"}
                  </button>
                </div>
              </form>
            </section>
          )}

          <section className="panel complaints-panel" id="complaints">
            <div className="panel-heading complaints-heading">
              <div>
                <h2>Recent complaints</h2>
                <p className="subtitle">
                  Review the latest campus support tickets.
                </p>
              </div>

              <label className="search-box">
                <span>⌕</span>
                <input
                  aria-label="Search complaints"
                  placeholder="Search tickets..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticket ID</th>
                    <th>Complaint</th>
                    <th>Category / Department</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Update Status</th>
                  </tr>
                </thead>

                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="empty-state">
                        Loading complaints from the database...
                      </td>
                    </tr>
                  ) : visibleComplaints.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="empty-state">
                        No matching complaints found.
                      </td>
                    </tr>
                  ) : (
                    visibleComplaints.map((complaint) => (
                      <tr key={complaint.id}>
                        <td>
                          <span className="ticket-id">
                            {complaint.ticket_id}
                          </span>
                        </td>

                        <td>
                          <strong>{complaint.title}</strong>
                          <span className="cell-subtitle">
                            {complaint.description}
                          </span>
                        </td>

                        <td>
                          <strong>{complaint.category}</strong>
                          <span className="cell-subtitle">
                            {complaint.department}
                          </span>
                        </td>

                        <td>{formatDate(complaint.submitted_at)}</td>

                        <td>
                          <span
                            className={`status ${complaint.status
                              .toLowerCase()
                              .replaceAll(" ", "-")}`}
                          >
                            <span className="status-dot"></span>
                            {complaint.status}
                          </span>
                        </td>

                        <td>
                          <select
                            aria-label={`Update status for ${complaint.ticket_id}`}
                            value={complaint.status}
                            disabled={updatingId === complaint.id}
                            onChange={(event) =>
                              updateComplaintStatus(
                                complaint.id,
                                event.target.value
                              )
                            }
                          >
                            {STATUSES.map((status) => (
                              <option key={status} value={status}>
                                {status}
                              </option>
                            ))}
                          </select>

                          {updatingId === complaint.id && (
                            <span className="cell-subtitle">
                              Saving...
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="table-footer">
              Showing {loading ? "—" : visibleComplaints.length} of{" "}
              {loading ? "—" : complaints.length} complaints

              <button
                className="secondary-button"
                type="button"
                onClick={loadComplaints}
                disabled={loading || updatingId !== null}
              >
                Refresh
              </button>
            </div>
          </section>

          <footer className="page-footer">
            <span>SmartCampus · Campus support made transparent</span>
            <span>Prototype v0.2</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
