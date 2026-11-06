
import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const STATUSES = ["Submitted", "In Progress", "Resolved", "Rejected"];
const RATINGS = [1, 2, 3, 4, 5];

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

function hasFeedback(complaint) {
  return (
    complaint.feedback_submitted_at != null ||
    complaint.feedback_rating != null ||
    (typeof complaint.feedback === "string" &&
      complaint.feedback.trim().length > 0)
  );
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

  const [feedbackText, setFeedbackText] = useState({});
  const [feedbackRating, setFeedbackRating] = useState({});
  const [feedbackSubmittingId, setFeedbackSubmittingId] = useState(null);

  const [adminFeedback, setAdminFeedback] = useState([]);
  const [feedbackAnalytics, setFeedbackAnalytics] = useState(null);
  const [adminFeedbackLoading, setAdminFeedbackLoading] = useState(false);
  const [adminFeedbackError, setAdminFeedbackError] = useState("");

  const isAdmin = user?.role === "admin";

  const logout = useCallback((message = "") => {
    sessionStorage.removeItem("smartcampus_token");
    setToken("");
    setUser(null);
    setComplaints([]);
    setAdminFeedback([]);
    setFeedbackAnalytics(null);
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
      if (
        err.message === "Not authenticated" ||
        err.message.toLowerCase().includes("token")
      ) {
        logout("Your session may have expired. Please log in again.");
      } else {
        setError(err.message || "Unable to load complaints.");
      }
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  const loadAdminFeedback = useCallback(async () => {
    if (!token || !isAdmin) return;

    setAdminFeedbackLoading(true);
    setAdminFeedbackError("");

    try {
      const [feedbackResponse, analyticsResponse] = await Promise.all([
        fetch(`${API_URL}/api/admin/feedback`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/admin/feedback/analytics`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      const [feedbackData, analyticsData] = await Promise.all([
        readResponse(feedbackResponse),
        readResponse(analyticsResponse),
      ]);

      setAdminFeedback(Array.isArray(feedbackData) ? feedbackData : []);
      setFeedbackAnalytics(analyticsData);
    } catch (err) {
      setAdminFeedbackError(
        err.message || "Unable to load feedback analytics."
      );
    } finally {
      setAdminFeedbackLoading(false);
    }
  }, [token, isAdmin]);

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

  useEffect(() => {
    if (user?.role === "admin" && token) {
      loadAdminFeedback();
    }
  }, [user, token, loadAdminFeedback]);

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

  const submitFeedback = async (event, complaint) => {
    event.preventDefault();

    const text = (feedbackText[complaint.id] || "").trim();
    const rating = feedbackRating[complaint.id] || 0;

    if (!rating) {
      setError("Please select a rating before submitting feedback.");
      return;
    }

    if (!text) {
      setError("Please enter your feedback.");
      return;
    }

    setNotice("");
    setError("");
    setFeedbackSubmittingId(complaint.id);

    try {
      await readResponse(
        await fetch(`${API_URL}/api/complaints/${complaint.id}/feedback`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            feedback: text,
            rating,
          }),
        })
      );

      setNotice(`Thank you! Feedback submitted for ${complaint.ticket_id}.`);
      setFeedbackText((previous) => ({
        ...previous,
        [complaint.id]: "",
      }));
      await loadComplaints();
    } catch (err) {
      setError(err.message || "Could not submit feedback.");
    } finally {
      setFeedbackSubmittingId(null);
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

  const analyticsTotal =
    feedbackAnalytics?.total_feedback ?? adminFeedback.length;
  const analyticsAverage = Number(
    feedbackAnalytics?.average_rating ?? 0
  );

  const ratingDistribution =
    feedbackAnalytics?.rating_distribution || {};

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
              {authMode === "login"
                ? "Sign in to your account"
                : "Create your account"}
            </h2>
            <p className="auth-subtitle">
              {authMode === "login"
                ? "Enter your details to access your campus dashboard."
                : "Register as a student to use the grievance portal."}
            </p>

            {notice && (
              <div className="notice" role="status">
                {notice}
              </div>
            )}
            {error && (
              <div className="auth-error" role="alert">
                {error}
              </div>
            )}

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
                  placeholder={
                    authMode === "register"
                      ? "At least 8 characters"
                      : "Enter your password"
                  }
                  autoComplete={
                    authMode === "login" ? "current-password" : "new-password"
                  }
                  minLength={authMode === "register" ? 8 : undefined}
                  maxLength={128}
                  required
                />
              </label>

              <button
                className="primary-button auth-submit"
                type="submit"
                disabled={authLoading}
              >
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Sign in →"
                    : "Create account →"}
              </button>
            </form>

            <p className="auth-switch">
              {authMode === "login"
                ? "New to SmartCampus?"
                : "Already have an account?"}
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

        {!isAdmin && (
          <button
            className="nav-item"
            type="button"
            onClick={() => {
              setNotice("");
              setError("");
              setShowForm(true);
              document
                .getElementById("new-complaint")
                ?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <span>＋</span> Submit Complaint
          </button>
        )}

        <button
          className="nav-item"
          type="button"
          onClick={() =>
            document
              .getElementById("complaints")
              ?.scrollIntoView({ behavior: "smooth" })
          }
        >
          <span>▤</span> {isAdmin ? "All Complaints" : "My Complaints"}
        </button>

        {isAdmin && (
          <button
            className="nav-item"
            type="button"
            onClick={() =>
              document
                .getElementById("feedback-analytics")
                ?.scrollIntoView({ behavior: "smooth" })
            }
          >
            <span>★</span> Feedback Analytics
          </button>
        )}

        <div className="sidebar-bottom">
          <div className="help-card">
            <div className="help-icon">?</div>
            <strong>Need help?</strong>
            <p>
              {isAdmin
                ? "Review campus complaints and monitor student feedback."
                : "Report an issue and we'll route it to the right department."}
            </p>
            {!isAdmin && (
              <button
                type="button"
                onClick={() => setShowForm(true)}
              >
                Report an issue →
              </button>
            )}
          </div>

          <div className="profile">
            <div className="avatar">
              {user.name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="profile-details">
              <strong>{user.name}</strong>
              <span>{user.role || "student"} account</span>
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
            <span className="topbar-user">{user.name}</span>
            <button
              className="secondary-button logout-button"
              type="button"
              onClick={() => logout("You have signed out.")}
            >
              Sign out
            </button>
          </div>
        </header>

        <section className="page-content">
          <div className="welcome-row">
            <div>
              <p className="eyebrow">
                {isAdmin ? "ADMINISTRATION CENTER" : "CAMPUS SUPPORT CENTER"}
              </p>
              <h1>
                Welcome, {user.name.split(" ")[0]}!{" "}
                <span className="wave">✳</span>
              </h1>
              <p className="subtitle">
                {isAdmin
                  ? "Monitor complaints, manage resolutions, and review student feedback."
                  : "Report issues, track progress, and help make your campus better."}
              </p>
            </div>

            {!isAdmin && (
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
            )}
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
            <div className="notice error-notice" role="alert">
              <span>!</span> {error}
              <button type="button" onClick={() => setError("")}>
                ×
              </button>
            </div>
          )}

          <div className="stats-grid">
            {stats.map((stat) => (
              <div className="stat-card" key={stat.label}>
                <div className={`stat-icon ${stat.color}`}>{stat.icon}</div>
                <div className="stat-label">{stat.label}</div>
                <div className="stat-value">
                  {loading ? "—" : stat.value}
                </div>
                <div className="stat-footnote">Based on saved tickets</div>
              </div>
            ))}
          </div>

          {!isAdmin && (
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
          )}

          {showForm && !isAdmin && (
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
                  onClick={() => {
                    setShowForm(false);
                    setSelectedImage(null);
                  }}
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
                  <span className="cell-subtitle">
                    JPG, PNG, or WEBP · Maximum 5 MB
                  </span>
                  {selectedImage && (
                    <span className="cell-subtitle">
                      Selected: {selectedImage.name}
                    </span>
                  )}
                </label>

                <div className="form-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setSelectedImage(null);
                    }}
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
                <h2>{isAdmin ? "All complaints" : "Recent complaints"}</h2>
                <p className="subtitle">
                  {isAdmin
                    ? "Review and manage campus support tickets."
                    : "Review the latest campus support tickets and submit feedback on resolved issues."}
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
                    {isAdmin && <th>Update Status</th>}
                    {!isAdmin && <th>Feedback</th>}
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

                        {isAdmin && (
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
                              <span className="cell-subtitle">Saving...</span>
                            )}
                          </td>
                        )}

                        {!isAdmin && (
                          <td className="feedback-table-cell">
                            {complaint.status !== "Resolved" ? (
                              <span className="feedback-pending">
                                Available after resolution
                              </span>
                            ) : hasFeedback(complaint) ? (
                              <div className="feedback-submitted">
                                <span className="feedback-stars">
                                  {"★".repeat(
                                    Math.max(
                                      0,
                                      Math.min(
                                        5,
                                        Number(complaint.feedback_rating) || 0
                                      )
                                    )
                                  )}
                                  {"☆".repeat(
                                    5 -
                                      Math.max(
                                        0,
                                        Math.min(
                                          5,
                                          Number(complaint.feedback_rating) || 0
                                        )
                                      )
                                  )}
                                </span>
                                <span>Submitted</span>
                              </div>
                            ) : (
                              <button
                                type="button"
                                className="feedback-open-button"
                                onClick={() => {
                                  document
                                    .getElementById(
                                      `feedback-${complaint.id}`
                                    )
                                    ?.scrollIntoView({
                                      behavior: "smooth",
                                      block: "center",
                                    });
                                }}
                              >
                                Give feedback ↓
                              </button>
                            )}
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="table-footer">
              <span>
                Showing {loading ? "—" : visibleComplaints.length} of{" "}
                {loading ? "—" : complaints.length} complaints
              </span>
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

          {!isAdmin && (
            <section className="feedback-section">
              <div className="section-intro">
                <p className="eyebrow">STUDENT EXPERIENCE</p>
                <h2>Share your feedback</h2>
                <p className="subtitle">
                  Your feedback helps improve campus services. You can submit
                  feedback once a complaint has been resolved.
                </p>
              </div>

              {complaints.filter(
                (complaint) =>
                  complaint.status === "Resolved" && !hasFeedback(complaint)
              ).length === 0 ? (
                <div className="panel feedback-empty">
                  <div className="feedback-empty-icon">★</div>
                  <strong>No pending feedback</strong>
                  <p>
                    When one of your complaints is resolved, you can rate the
                    service and share your experience here.
                  </p>
                </div>
              ) : (
                <div className="feedback-card-list">
                  {complaints
                    .filter(
                      (complaint) =>
                        complaint.status === "Resolved" &&
                        !hasFeedback(complaint)
                    )
                    .map((complaint) => (
                      <form
                        className="panel feedback-form-card"
                        id={`feedback-${complaint.id}`}
                        key={complaint.id}
                        onSubmit={(event) =>
                          submitFeedback(event, complaint)
                        }
                      >
                        <div className="feedback-card-heading">
                          <div>
                            <span className="ticket-id">
                              {complaint.ticket_id}
                            </span>
                            <h3>{complaint.title}</h3>
                            <p className="subtitle">
                              Resolved · {complaint.department}
                            </p>
                          </div>
                          <span className="status resolved">
                            <span className="status-dot"></span>
                            Resolved
                          </span>
                        </div>

                        <label className="rating-label">
                          How would you rate the resolution?
                          <div
                            className="rating-picker"
                            role="group"
                            aria-label={`Rating for ${complaint.ticket_id}`}
                          >
                            {RATINGS.map((rating) => (
                              <button
                                type="button"
                                key={rating}
                                className={`rating-star ${
                                  (feedbackRating[complaint.id] || 0) >= rating
                                    ? "selected"
                                    : ""
                                }`}
                                aria-label={`${rating} out of 5 stars`}
                                aria-pressed={
                                  feedbackRating[complaint.id] === rating
                                }
                                onClick={() =>
                                  setFeedbackRating((previous) => ({
                                    ...previous,
                                    [complaint.id]: rating,
                                  }))
                                }
                              >
                                ★
                              </button>
                            ))}
                            <span className="rating-hint">
                              {feedbackRating[complaint.id]
                                ? `${feedbackRating[complaint.id]} / 5`
                                : "Select a rating"}
                            </span>
                          </div>
                        </label>

                        <label>
                          Your comments
                          <textarea
                            rows={3}
                            minLength={1}
                            maxLength={1000}
                            placeholder="Tell us about your experience with the resolution..."
                            value={feedbackText[complaint.id] || ""}
                            onChange={(event) =>
                              setFeedbackText((previous) => ({
                                ...previous,
                                [complaint.id]: event.target.value,
                              }))
                            }
                            required
                          />
                          <span className="cell-subtitle">
                            Maximum 1000 characters
                          </span>
                        </label>

                        <div className="form-actions">
                          <button
                            className="primary-button"
                            type="submit"
                            disabled={
                              feedbackSubmittingId === complaint.id
                            }
                          >
                            {feedbackSubmittingId === complaint.id
                              ? "Submitting..."
                              : "Submit feedback →"}
                          </button>
                        </div>
                      </form>
                    ))}
                </div>
              )}
            </section>
          )}

          {isAdmin && (
            <section
              className="admin-feedback-section"
              id="feedback-analytics"
            >
              <div className="section-intro">
                <p className="eyebrow">STUDENT EXPERIENCE</p>
                <h2>Feedback analytics</h2>
                <p className="subtitle">
                  Review student ratings and feedback across resolved
                  complaints.
                </p>
              </div>

              {adminFeedbackError && (
                <div className="notice error-notice" role="alert">
                  {adminFeedbackError}
                  <button
                    type="button"
                    onClick={() => setAdminFeedbackError("")}
                  >
                    ×
                  </button>
                </div>
              )}

              <div className="analytics-grid">
                <div className="panel analytics-card">
                  <div className="analytics-icon blue">▤</div>
                  <span className="stat-label">Total feedback</span>
                  <strong className="analytics-value">
                    {adminFeedbackLoading ? "—" : analyticsTotal}
                  </strong>
                  <span className="stat-footnote">
                    Student submissions
                  </span>
                </div>

                <div className="panel analytics-card">
                  <div className="analytics-icon orange">★</div>
                  <span className="stat-label">Average rating</span>
                  <strong className="analytics-value">
                    {adminFeedbackLoading
                      ? "—"
                      : analyticsTotal
                        ? analyticsAverage.toFixed(1)
                        : "0.0"}
                    <span className="out-of-five"> / 5</span>
                  </strong>
                  <span className="stat-footnote">
                    Across submitted feedback
                  </span>
                </div>
              </div>

              <div className="panel rating-distribution-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Rating distribution</h3>
                    <p className="subtitle">
                      Number of feedback submissions for each rating.
                    </p>
                  </div>
                </div>

                <div className="rating-bars">
                  {RATINGS.slice().reverse().map((rating) => {
                    const count =
                      Number(
                        ratingDistribution[rating] ??
                          ratingDistribution[String(rating)] ??
                          0
                      ) || 0;
                    const percentage = analyticsTotal
                      ? Math.min(100, (count / analyticsTotal) * 100)
                      : 0;

                    return (
                      <div className="rating-bar-row" key={rating}>
                        <span className="rating-bar-label">
                          {rating} <span>★</span>
                        </span>
                        <div className="rating-bar-track">
                          <div
                            className="rating-bar-fill"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <strong>{adminFeedbackLoading ? "—" : count}</strong>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="panel admin-feedback-list">
                <div className="panel-heading admin-feedback-heading">
                  <div>
                    <h3>Recent student feedback</h3>
                    <p className="subtitle">
                      Feedback received for resolved complaints.
                    </p>
                  </div>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={loadAdminFeedback}
                    disabled={adminFeedbackLoading}
                  >
                    {adminFeedbackLoading ? "Refreshing..." : "Refresh"}
                  </button>
                </div>

                {adminFeedbackLoading ? (
                  <div className="empty-state">
                    Loading student feedback...
                  </div>
                ) : adminFeedback.length === 0 ? (
                  <div className="empty-state">
                    No feedback submissions are available yet.
                  </div>
                ) : (
                  <div className="admin-feedback-items">
                    {adminFeedback.map((item, index) => {
                      const rating = Math.max(
                        0,
                        Math.min(5, Number(item.rating) || 0)
                      );

                      return (
                        <article
                          className="admin-feedback-item"
                          key={`${item.complaint_id ?? index}-${index}`}
                        >
                          <div className="admin-feedback-item-top">
                            <div>
                              <span className="ticket-id">
                                {item.ticket_id || `Complaint #${item.complaint_id}`}
                              </span>
                              <h4>{item.title || "Campus complaint"}</h4>
                              <span className="cell-subtitle">
                                {item.student_name || "Student"} ·{" "}
                                {formatDate(item.feedback_submitted_at)}
                              </span>
                            </div>
                            <span className="feedback-stars">
                              {"★".repeat(rating)}
                              {"☆".repeat(5 - rating)}
                            </span>
                          </div>
                          <p className="admin-feedback-comment">
                            {item.feedback}
                          </p>
                        </article>
                      );
                    })}
                  </div>
                )}
              </div>
            </section>
          )}

          <footer className="page-footer">
            <span>SmartCampus · Campus support made transparent</span>
            <span>Prototype v0.4</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
