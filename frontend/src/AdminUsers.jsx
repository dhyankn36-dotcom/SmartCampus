
import { useCallback, useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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

export default function AdminUsers({ token, user }) {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadUsers = useCallback(async () => {
    if (!token || user?.role !== "admin") return;

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        page: "1",
        page_size: "50",
      });

      if (search.trim()) {
        params.set("search", search.trim());
      }

      if (roleFilter !== "all") {
        params.set("role", roleFilter);
      }

      const response = await fetch(
        `${API_URL}/api/admin/users?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await readResponse(response);
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Unable to load users.");
    } finally {
      setLoading(false);
    }
  }, [token, user?.role, search, roleFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const changeRole = async (targetUser, newRole) => {
    if (targetUser.id === user?.id) {
      setError("You cannot change your own administrator role.");
      return;
    }

    const action =
      newRole === "admin" ? "promote this user to admin" : "demote this admin to student";

    const confirmed = window.confirm(
      `Are you sure you want to ${action}?\n\n${targetUser.name} (${targetUser.email})`
    );

    if (!confirmed) return;

    setUpdatingId(targetUser.id);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/api/admin/users/${targetUser.id}/role`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ role: newRole }),
        }
      );

      const result = await readResponse(response);

      setMessage(
        result.message ||
          `${targetUser.name}'s role was updated successfully.`
      );

      await loadUsers();
    } catch (err) {
      setError(err.message || "Unable to update the user's role.");
    } finally {
      setUpdatingId(null);
    }
  };

  if (user?.role !== "admin") return null;

  return (
    <section className="panel admin-users-section" id="admin-users">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>User Management</h2>
          <p className="subtitle">
            View registered accounts and manage administrator permissions.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadUsers}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh users"}
        </button>
      </div>

      {message && (
        <div className="admin-users-message" role="status">
          {message}
          <button type="button" onClick={() => setMessage("")}>×</button>
        </div>
      )}

      {error && (
        <div className="admin-users-error" role="alert">
          {error}
          <button type="button" onClick={() => setError("")}>×</button>
        </div>
      )}

      <div className="admin-users-toolbar">
        <label className="search-box">
          <span>⌕</span>
          <input
            type="search"
            placeholder="Search name or email..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <select
          className="admin-role-filter"
          value={roleFilter}
          onChange={(event) => setRoleFilter(event.target.value)}
          aria-label="Filter users by role"
        >
          <option value="all">All roles</option>
          <option value="student">Students</option>
          <option value="admin">Administrators</option>
        </select>
      </div>

      <div className="admin-users-summary">
        <span>
          Showing <strong>{users.length}</strong> account(s)
        </span>
        <span>Maximum 50 accounts per request</span>
      </div>

      <div className="table-wrap admin-users-table-wrap">
        <table className="admin-users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Registered</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="empty-state">
                  Loading registered users...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan="5" className="empty-state">
                  No users match your search.
                </td>
              </tr>
            ) : (
              users.map((targetUser) => {
                const isCurrentUser = targetUser.id === user?.id;
                const isAdmin = targetUser.role === "admin";
                const isUpdating = updatingId === targetUser.id;

                return (
                  <tr key={targetUser.id}>
                    <td>
                      <div className="admin-user-name">
                        <span className="admin-user-avatar">
                          {targetUser.name?.charAt(0)?.toUpperCase() || "U"}
                        </span>
                        <strong>{targetUser.name}</strong>
                      </div>
                    </td>

                    <td>{targetUser.email}</td>

                    <td>
                      <span
                        className={`role-pill ${
                          isAdmin ? "admin" : "student"
                        }`}
                      >
                        {isAdmin ? "Administrator" : "Student"}
                      </span>
                    </td>

                    <td>{formatDate(targetUser.created_at)}</td>

                    <td>
                      {isCurrentUser ? (
                        <span className="user-current-account">
                          Current account
                        </span>
                      ) : (
                        <button
                          type="button"
                          className={`user-action-button ${
                            isAdmin ? "demote" : "promote"
                          }`}
                          disabled={updatingId !== null}
                          onClick={() =>
                            changeRole(
                              targetUser,
                              isAdmin ? "student" : "admin"
                            )
                          }
                        >
                          {isUpdating
                            ? "Updating..."
                            : isAdmin
                              ? "Demote"
                              : "Promote"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
