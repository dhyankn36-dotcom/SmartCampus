
import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const STATUSES = ["Submitted", "In Progress", "Resolved", "Rejected"];

const emptyForm = {
  title: "",
  category: "Infrastructure",
  location: "",
  description: "",
};

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be completed."
    );
  }

  return data;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
}

function App() {
  const [token, setToken] = useState(
    () => sessionStorage.getItem("smartcampus_token") || ""
  );
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [authLoading, setAuthLoading] = useState(false);

  const [complaints, setComplaints] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [selectedImage, setSelectedImage] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);

  const logout = useCallback((message = "") => {
    sessionStorage.removeItem("smartcampus_token");
    setToken("");
    setUser(null);
    setComplaints([]);
    setNotice(message);
    setError("");
    setShowForm(false);
    setSelectedImage(null);
  }, []);

  const authHeaders = useCallback(
    () => ({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    [token]
  );

  const loadComplaints = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/complaints`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await readResponse(response);
      setComplaints(data);
    } catch (err) {
      if (err.message === "Not authenticated" || err.message.includes("token")) {
        logout("Your session may have expired. Please log in again.");
      } else {
        setError(err.message || "Unable to load complaints.");
      }
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setComplaints([]);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function verifySession() {
      try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const currentUser = await readResponse(response);

        if (!cancelled) setUser(currentUser);
      } catch {
        if (!cancelled) logout("Please log in to continue.");
      }
    }

    verifySession();

    return () => {
      cancelled = true;
    };
  }, [token, logout]);

  useEffect(() => {
    if (user && token) loadComplaints();
  }, [user, token, loadComplaints]);

  const updateAuthField = (event) => {
    const { name, value } = event.target;
    setAuthForm((previous) => ({ ...previous, [name]: value }));
  };

  const submitAuth = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    setAuthLoading(true);

    try {
      if (authMode === "register") {
        await readResponse(
          await fetch(`${API_URL}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: authForm.name.trim(),
              email: authForm.email.trim(),
              password: authForm.password,
            }),
          })
        );
      }

      const result = await readResponse(
        await fetch(`${API_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: authForm.email.trim(),
            password: authForm.password,
          }),
        })
      );

      sessionStorage.setItem("smartcampus_token", result.access_token);
      setUser(result.user);
      setToken(result.access_token);
      setAuthForm({ name: "", email: "", password: "" });
      setNotice(
        authMode === "register"
          ? "Account created successfully. Welcome to SmartCampus!"
          : `Welcome back, ${result.user.name}!`
      );
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setAuthLoading(false);
    }
  };

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

      const result = await readResponse(
        await fetch(`${API_URL}/api/complaints`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            title: form.title.trim(),
            description,
            category: form.category,
          }),
        })
      );

      let successMessage = `Complaint ${result.ticket_id} submitted successfully!`;

      // Upload an optional image after the complaint is created.
      if (selectedImage) {
        const imageBody = new FormData();
        imageBody.append("file", selectedImage);

        try {
          await readResponse(
            await fetch(`${API_URL}/api/complaints/${result.id}/image`, {
              method: "POST",
              headers: { Authorization: `Bearer ${token}` },
              body: imageBody,
            })
          );
          successMessage += " Image uploaded successfully.";
        } catch (imageError) {
          successMessage += ` Complaint saved, but image upload failed: ${imageError.message}`;
        }
      }

      setForm(emptyForm);
      setSelectedImage(null);
      setShowForm(false);
      setNotice(successMessage);
      await loadComplaints();
    } catch (err) {
      setError(err.message || "Could not submit the complaint.");
    } finally {
      setSubmitting(false);
    }
  };

  const updateComplaintStatus = async (complaintId, newStatus) => {
    setNotice("");
    setError("");
    setUpdatingId(complaintId);

    try {
      const result = await readResponse(
        await fetch(`${API_URL}/api/complaints/${complaintId}/status`, {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({ status: newStatus }),
        })
      );

      setNotice(`${result.ticket_id}: status changed to ${result.status}.`);
      await loadComplaints();
    } catch (err) {
      setError(err.message || "Could not update the complaint status.");
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

  if (!token || !user) {
    return (
      <div className="auth-page">
        <section className="auth-brand-panel">
          <div className="brand">
            <div className="brand-icon">SC</div>
            <div>
              <h2>SmartCampus</h2>
              <span>Grievance Portal</span>
            </div>
          </div>

          <div className="auth-promo">
            <span className="auth-kicker">CAMPUS SUPPORT CENTER</span>
            <h1>A better campus starts with being heard.</h1>
            <p>
              Report campus issues, track your tickets, and stay informed
              about their progress in one place.
            </p>
            <div className="auth-feature">
              <span>✓</span>
              <div>
                <strong>Simple reporting</strong>
                <p>Submit concerns with clear details.</p>
              </div>
            </div>
            <div className="auth-feature">
              <span>↗</span>
              <div>
                <strong>Transparent tracking</strong>
                <p>Keep track of complaint status.</p>
              </div>
            </div>
          </div>

          <p className="auth-panel-footer">
            SmartCampus · Campus support made transparent
          </p>
        </section>

        <main className="auth-main">
          <div className="auth-card">
            <div className="auth-mobile-brand">
              <div className="brand-icon">SC</div>
              <strong>SmartCampus</strong>
            </div>

            <p className="eyebrow">
              {authMode === "login" ? "WELCOME BACK" : "GET STARTED"}
            </p>
            <h2>
              {authMode === "login" ? "Sign in to your account" : "Create your account"}
            </h2>
            <p className="auth-subtitle">
              {authMode === "login"
                ? "Enter your details to access your campus dashboard."
                : "Register as a student to use the grievance portal."}
            </p>

            {notice && <div className="notice" role="status">{notice}</div>}
            {error && <div className="auth-error" role="alert">{error}</div>}

            <form onSubmit={submitAuth}>
              {authMode === "register" && (
                <label>
                  Full name
                  <input
                    name="name"
                    value={authForm.name}
                    onChange={updateAuthField}
                    placeholder="Enter your full name"
                    autoComplete="name"
                    minLength={2}
                    maxLength={100}
                    required
                  />
                </label>
              )}

              <label>
                Email address
                <input
                  type="email"
                  name="email"
                  value={authForm.email}
                  onChange={updateAuthField}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </label>

              <label>
                Password
                <input
                  type="password"
                  name="password"
                  value={authForm.password}
                  onChange={updateAuthField}
                  placeholder={authMode === "register" ? "At least 8 characters" : "Enter your password"}
                  autoComplete={authMode === "login" ? "current-password" : "new-password"}
                  minLength={authMode === "register" ? 8 : undefined}
                  maxLength={128}
                  required
                />
              </label>

              <button className="primary-button auth-submit" type="submit" disabled={authLoading}>
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Sign in →"
                    : "Create account →"}
              </button>
            </form>

            <p className="auth-switch">
              {authMode === "login" ? "New to SmartCampus?" : "Already have an account?"}
              <button
                type="button"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "register" : "login");
                  setError("");
                  setNotice("");
                }}
              >
                {authMode === "login" ? "Create an account" : "Sign in"}
              </button>
            </p>

            <p className="auth-security">
              Your account is authenticated by the SmartCampus server.
            </p>
          </div>
        </main>
      </div>
    );
  }

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
          onClick={() => document.getElementById("complaints")?.scrollIntoView({ behavior: "smooth" })}
        >
          <span>▤</span> My Complaints
        </button>

        <div className="sidebar-bottom">
          <div className="help-card">
            <div className="help-icon">?</div>
            <strong>Need help?</strong>
            <p>Report an issue and we'll route it to the right department.</p>
            <button type="button" onClick={() => setShowForm(true)}>
              Report an issue →
            </button>
          </div>

          <div className="profile">
            <div className="avatar">{user.name?.charAt(0)?.toUpperCase() || "U"}</div>
            <div className="profile-details">
              <strong>{user.name}</strong>
              <span>{user.role || "student"} account</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> Dashboard</div>
          <div className="topbar-right">
            <span className="live-dot"></span>
            <span className="system-status">Campus services portal</span>
            <span className="topbar-user">{user.name}</span>
            <button className="secondary-button logout-button" type="button" onClick={() => logout("You have signed out.")}>
              Sign out
            </button>
          </div>
        </header>

        <section className="page-content">
          <div className="welcome-row">
            <div>
              <p className="eyebrow">CAMPUS SUPPORT CENTER</p>
              <h1>Welcome, {user.name.split(" ")[0]}! <span className="wave">✳</span></h1>
              <p className="subtitle">Report issues, track progress, and help make your campus better.</p>
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
              <button type="button" onClick={() => setNotice("")}>×</button>
            </div>
          )}
          {error && (
            <div className="notice" role="alert">
              <span>!</span> {error}
              <button type="button" onClick={() => setError("")}>×</button>
            </div>
          )}

          <div className="stats-grid">
            {stats.map((stat) => (
              <div className="stat-card" key={stat.label}>
                <div className={`stat-icon ${stat.color}`}>{stat.icon}</div>
                <div className="stat-label">{stat.label}</div>
                <div className="stat-value">{loading ? "—" : stat.value}</div>
                <div className="stat-footnote">Based on saved tickets</div>
              </div>
            ))}
          </div>

          <section className="panel quick-panel">
            <div>
              <div className="panel-icon">✦</div>
              <div>
                <h3>Have something that needs attention?</h3>
                <p>Tell us what's happening. Your complaint will be routed to the appropriate department.</p>
              </div>
            </div>
            <button className="secondary-button" type="button" onClick={() => setShowForm(true)}>
              Create a ticket <span>→</span>
            </button>
          </section>

          {showForm && (
            <section className="panel form-panel" id="new-complaint">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">NEW TICKET</p>
                  <h2>Submit a complaint</h2>
                  <p className="subtitle">Provide accurate details so the right team can help.</p>
                </div>
                <button className="close-button" type="button" onClick={() => { setShowForm(false); setSelectedImage(null); }} aria-label="Close form">×</button>
              </div>

              <form onSubmit={submitComplaint}>
                <label>
                  Complaint title
                  <input name="title" value={form.title} onChange={updateField} placeholder="e.g. Wi-Fi not working in Block A" required minLength={3} maxLength={200} />
                </label>

                <div className="form-grid">
                  <label>
                    Category
                    <select name="category" value={form.category} onChange={updateField}>
                      <option>Infrastructure</option>
                      <option>Wi-Fi</option>
                      <option>Cleanliness</option>
                      <option>Transport</option>
                    </select>
                  </label>
                  <label>
                    Location
                    <input name="location" value={form.location} onChange={updateField} placeholder="e.g. Block A, Room 204" required />
                  </label>
                </div>

                <label>
                  Description
                  <textarea name="description" value={form.description} onChange={updateField} placeholder="Describe the issue and when you noticed it..." rows={4} required minLength={5} maxLength={2000} />
                </label>

                <label>
                  Attach an image (optional)
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={(event) => {
                      const file = event.target.files?.[0] || null;
                      if (file && file.size > 5 * 1024 * 1024) {
                        setError("Image must be 5 MB or smaller.");
                        event.target.value = "";
                        setSelectedImage(null);
                        return;
                      }
                      setError("");
                      setSelectedImage(file);
                    }}
                    disabled={submitting}
                  />
                  <span className="cell-subtitle">JPG, PNG, or WEBP · Maximum 5 MB</span>
                  {selectedImage && (
                    <span className="cell-subtitle">Selected: {selectedImage.name}</span>
                  )}
                </label>

                <div className="form-actions">
                  <button className="secondary-button" type="button" onClick={() => { setShowForm(false); setSelectedImage(null); }} disabled={submitting}>Cancel</button>
                  <button className="primary-button" type="submit" disabled={submitting}>
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
                <p className="subtitle">Review the latest campus support tickets.</p>
              </div>
              <label className="search-box">
                <span>⌕</span>
                <input aria-label="Search complaints" placeholder="Search tickets..." value={search} onChange={(event) => setSearch(event.target.value)} />
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
                    <tr><td colSpan="6" className="empty-state">Loading complaints from the database...</td></tr>
                  ) : visibleComplaints.length === 0 ? (
                    <tr><td colSpan="6" className="empty-state">No matching complaints found.</td></tr>
                  ) : (
                    visibleComplaints.map((complaint) => (
                      <tr key={complaint.id}>
                        <td><span className="ticket-id">{complaint.ticket_id}</span></td>
                        <td>
                          <strong>{complaint.title}</strong>
                          <span className="cell-subtitle">{complaint.description}</span>
                          {complaint.image_url && (
                            <a
                              href={`${API_URL}${complaint.image_url}`}
                              target="_blank"
                              rel="noreferrer"
                              className="cell-subtitle"
                            >
                              View attached image
                            </a>
                          )}
                        </td>
                        <td>
                          <strong>{complaint.category}</strong>
                          <span className="cell-subtitle">{complaint.department}</span>
                        </td>
                        <td>{formatDate(complaint.submitted_at)}</td>
                        <td>
                          <span className={`status ${complaint.status.toLowerCase().replaceAll(" ", "-")}`}>
                            <span className="status-dot"></span>
                            {complaint.status}
                          </span>
                        </td>
                        <td>
                          <select
                            aria-label={`Update status for ${complaint.ticket_id}`}
                            value={complaint.status}
                            disabled={updatingId === complaint.id}
                            onChange={(event) => updateComplaintStatus(complaint.id, event.target.value)}
                          >
                            {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
                          </select>
                          {updatingId === complaint.id && <span className="cell-subtitle">Saving...</span>}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="table-footer">
              Showing {loading ? "—" : visibleComplaints.length} of {loading ? "—" : complaints.length} complaints
              <button className="secondary-button" type="button" onClick={loadComplaints} disabled={loading || updatingId !== null}>Refresh</button>
            </div>
          </section>

          <footer className="page-footer">
            <span>SmartCampus · Campus support made transparent</span>
            <span>Prototype v0.3</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
