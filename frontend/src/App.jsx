import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const defaultEmployee = {
  first_name: "",
  last_name: "",
  email: "",
  role: "EMPLOYEE",
  base_salary: "",
  payment_date: "28",
  leaves_allowed: "24"
};

const defaultLeaveForm = {
  start_date: "",
  end_date: "",
  reason: ""
};

const defaultPaymentForm = {
  amount: "",
  status: "PAID"
};

const defaultPlatformBillingForm = {
  company_id: "",
  amount: "",
  status: "PENDING"
};

const authDefaults = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  company_id: ""
};

const landingMetrics = [
  { label: "active employees", value: "12k+" },
  { label: "departments tracked", value: "48" },
  { label: "leave requests resolved", value: "99.2%" }
];

const landingFeatures = [
  {
    title: "Unified employee directory",
    text: "Find people fast with searchable profiles, departments, and contact details in one place.",
    icon: "M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v12.8a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.3V5.5Zm3.4 3v2.8h3.1V8.5H7.4Zm5.1 0v2.8h4.1V8.5h-4.1Zm-5.1 4.8v2.8h9.2v-2.8H7.4Z"
  },
  {
    title: "Leave and approval flows",
    text: "Track requests, approvals, balances, and history without bouncing between tools.",
    icon: "M6 3.8h12a1.7 1.7 0 0 1 1.7 1.7v13A1.7 1.7 0 0 1 18 20.2H6a1.7 1.7 0 0 1-1.7-1.7v-13A1.7 1.7 0 0 1 6 3.8Zm1.8 4.1v2h8.4v-2H7.8Zm0 4.1v2h4.8v-2H7.8Zm7 0v2h1.4v-2h-1.4Zm-7 4.1v1.5h8.4v-1.5H7.8Z"
  },
  {
    title: "Payroll snapshots",
    text: "Keep salary records, payment dates, and compensation summaries ready for review.",
    icon: "M7 4.2h10A1.8 1.8 0 0 1 18.8 6v12A1.8 1.8 0 0 1 17 19.8H7A1.8 1.8 0 0 1 5.2 18V6A1.8 1.8 0 0 1 7 4.2Zm1.2 4.1v2.4h7.6V8.3H8.2Zm0 4.2v2.4H13v-2.4H8.2Z"
  },
  {
    title: "Role-based access",
    text: "Company admins manage records while employees stay focused on their own information.",
    icon: "M12 2.4 5.3 5.2v5.2c0 4.4 2.8 8.5 6.7 10.2 3.9-1.7 6.7-5.8 6.7-10.2V5.2L12 2.4Zm0 4.2a2.7 2.7 0 0 1 2.7 2.7v1.1h.2a1.1 1.1 0 0 1 1.1 1.1v4.1a1.1 1.1 0 0 1-1.1 1.1H9.1A1.1 1.1 0 0 1 8 15.6v-4.1a1.1 1.1 0 0 1 1.1-1.1h.2V9.3A2.7 2.7 0 0 1 12 6.6Zm0 1.8a.9.9 0 0 0-.9.9v1.1h1.8V9.3a.9.9 0 0 0-.9-.9Z"
  }
];

const workflowSteps = [
  {
    title: "Onboard a company",
    text: "Create a new workspace, assign an admin, and start organizing records immediately."
  },
  {
    title: "Invite employees",
    text: "Employees join the right company workspace and only see the records they need."
  },
  {
    title: "Run the day-to-day",
    text: "Approve leave, review payroll snapshots, and keep the directory accurate."
  }
];

function LogoIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img">
      <path d="M7.5 9.2a3.7 3.7 0 1 0 0-7.4 3.7 3.7 0 0 0 0 7.4Zm9 0a3.7 3.7 0 1 0 0-7.4 3.7 3.7 0 0 0 0 7.4ZM2.7 22.2h9.6v-1.3c0-3.2-2.2-5.8-4.8-5.8s-4.8 2.6-4.8 5.8v1.3Zm9-7.1c1.1 1.4 1.8 3.4 1.8 5.8v1.3h7.8v-1.3c0-3.2-2.2-5.8-4.8-5.8-1.4 0-2.6.7-3.5 1.9-.4-.7-.8-1.3-1.3-1.9Z" />
    </svg>
  );
}

function roleLabel(role) {
  if (role === "SUPER_ADMIN") return "Platform admin";
  if (role === "COMPANY_ADMIN") return "Company admin";
  if (role === "EMPLOYEE") return "Employee";
  return role || "Guest";
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  });
}

function statusClass(status) {
  return String(status || "").toLowerCase();
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState(authDefaults);
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [employeeForm, setEmployeeForm] = useState(defaultEmployee);
  const [editingEmployeeId, setEditingEmployeeId] = useState(null);
  const [activePage, setActivePage] = useState("overview");
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [leaveForm, setLeaveForm] = useState(defaultLeaveForm);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [leaveBalance, setLeaveBalance] = useState(null);
  const [payrollSummary, setPayrollSummary] = useState(null);
  const [billingLedger, setBillingLedger] = useState([]);
  const [paymentForm, setPaymentForm] = useState(defaultPaymentForm);
  const [platformCompanies, setPlatformCompanies] = useState([]);
  const [platformLedger, setPlatformLedger] = useState([]);
  const [platformBillingForm, setPlatformBillingForm] = useState(defaultPlatformBillingForm);

  const canEdit = useMemo(() => user?.role === "COMPANY_ADMIN", [user]);
  const isCompanyAdmin = useMemo(() => user?.role === "COMPANY_ADMIN", [user]);

  useEffect(() => {
    if (!token || user?.role === "SUPER_ADMIN") return;
    loadEmployees();
  }, [token, user?.role, page, search, sortBy, sortOrder]);

  useEffect(() => {
    if (!token || user?.role === "SUPER_ADMIN") return;
    if (activePage === "leave") {
      loadLeaveData();
    }
    if (activePage === "payroll" && isCompanyAdmin) {
      loadPayrollData();
    }
  }, [token, user?.role, activePage, isCompanyAdmin]);

  useEffect(() => {
    if (user?.role === "EMPLOYEE" && activePage === "overview") {
      setActivePage("leave");
    }
    if (user?.role === "SUPER_ADMIN" && activePage !== "platform") {
      setActivePage("platform");
    }
  }, [user, activePage]);

  useEffect(() => {
    if (!token || user?.role !== "SUPER_ADMIN" || activePage !== "platform") return;
    loadPlatformData();
  }, [token, user?.role, activePage]);

  const visibleEmployees = employees;

  async function loadEmployees() {
    setLoading(true);
    setError("");
    try {
      const response = await api.listEmployees(
        { page: String(page), page_size: "10", search, sort_by: sortBy, sort_order: sortOrder },
        token
      );
      setEmployees(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadLeaveData() {
    setLoading(true);
    setError("");
    try {
      const [requests, balance] = await Promise.all([
        isCompanyAdmin ? api.getCompanyLeaveRequests(token) : api.getMyLeaveRequests(token),
        user?.id ? api.getLeaveBalance(user.id, token) : Promise.resolve(null)
      ]);
      setLeaveRequests(requests);
      setLeaveBalance(balance);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadPayrollData() {
    setLoading(true);
    setError("");
    try {
      const [summary, ledger] = await Promise.all([
        api.getPayrollSummary(token),
        api.getCompanyBillingLedger(token)
      ]);
      setPayrollSummary(summary);
      setBillingLedger(ledger);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitLeaveRequest(event) {
    event.preventDefault();
    setError("");
    try {
      await api.requestLeave(leaveForm, token);
      setLeaveForm(defaultLeaveForm);
      await loadLeaveData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function approveLeaveRequest(id, status) {
    setError("");
    try {
      await api.approveLeave(id, status, token);
      await loadLeaveData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function simulatePaymentRun(event) {
    event.preventDefault();
    setError("");
    try {
      await api.simulateCompanyPayment(paymentForm, token);
      setPaymentForm(defaultPaymentForm);
      await loadPayrollData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadPlatformData() {
    setLoading(true);
    setError("");
    try {
      const [companies, ledger] = await Promise.all([
        api.listCompanies(token),
        api.getBillingLedger(token)
      ]);
      setPlatformCompanies(companies);
      setPlatformLedger(ledger);
      setPlatformBillingForm((current) => ({
        ...current,
        company_id: current.company_id || companies[0]?.id || ""
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function togglePlatformCompanyStatus(companyId) {
    setError("");
    try {
      await api.toggleCompanyStatus(companyId, token);
      await loadPlatformData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function recordOrchardBilling(event) {
    event.preventDefault();
    setError("");
    try {
      await api.simulateBilling(platformBillingForm, token);
      setPlatformBillingForm({
        ...defaultPlatformBillingForm,
        company_id: platformBillingForm.company_id
      });
      await loadPlatformData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      if (authMode === "login") {
        const response = await api.login({ email: authForm.email, password: authForm.password });
        setToken(response.data.access_token);
        setUser(response.data.user);
        setSelectedEmployee(null);
        setActivePage(
          response.data.user?.role === "SUPER_ADMIN"
            ? "platform"
            : response.data.user?.role === "EMPLOYEE"
              ? "leave"
              : "overview"
        );
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("user", JSON.stringify(response.data.user));
        setShowAuthModal(false);
      } else {
        const response = await api.signup(
          {
            email: authForm.email,
            password: authForm.password,
            first_name: authForm.first_name || "First",
            last_name: authForm.last_name || "Last",
            role: authMode === "company" ? "ADMIN" : "USER"
          },
          authMode === "company" ? undefined : authForm.company_id
        );
        setToken(response.data.access_token);
        setUser(response.data.user);
        setSelectedEmployee(null);
        setActivePage(
          response.data.user?.role === "SUPER_ADMIN"
            ? "platform"
            : response.data.user?.role === "EMPLOYEE"
              ? "leave"
              : "overview"
        );
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("user", JSON.stringify(response.data.user));
        setShowAuthModal(false);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  function openAuth(nextMode = "login") {
    setAuthMode(nextMode);
    setError("");
    setAuthForm(authDefaults);
    setShowAuthModal(true);
  }

  function clearDirectoryFilters() {
    setSearch("");
    setSortBy("name");
    setSortOrder("asc");
    setPage(1);
  }

  async function createEmployee(event) {
    event.preventDefault();
    if (!canEdit) return;
    try {
      await api.createEmployee(employeeForm, token);
      setEmployeeForm(defaultEmployee);
      setShowModal(false);
      await loadEmployees();
    } catch (err) {
      setError(err.message);
    }
  }

  async function updateEmployee(event) {
    event.preventDefault();
    if (!canEdit || !editingEmployeeId) return;
    try {
      await api.updateEmployee(editingEmployeeId, employeeForm, token);
      setEmployeeForm(defaultEmployee);
      setEditingEmployeeId(null);
      setShowModal(false);
      await loadEmployees();
      if (selectedEmployee && selectedEmployee.id === editingEmployeeId) {
        await viewEmployeeDetails(editingEmployeeId);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteEmployee(id) {
    if (!canEdit) return;
    try {
      await api.deleteEmployee(id, token);
      await loadEmployees();
    } catch (err) {
      setError(err.message);
    }
  }

  async function viewEmployeeDetails(employeeId) {
    try {
      const response = await api.getEmployee(employeeId, token);
      setSelectedEmployee(response.data);
      setActivePage("details");
    } catch (err) {
      setError(err.message);
    }
  }

  function openModal(employee = null) {
    if (employee) {
      setEditingEmployeeId(employee.id);
      setEmployeeForm({
        first_name: employee.first_name || "",
        last_name: employee.last_name || "",
        email: employee.email,
        role: employee.role || "EMPLOYEE",
        base_salary: employee.base_salary ?? "",
        payment_date: employee.payment_date ?? "28",
        leaves_allowed: employee.leaves_allowed ?? "24"
      });
    } else {
      setEditingEmployeeId(null);
      setEmployeeForm(defaultEmployee);
    }
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingEmployeeId(null);
    setEmployeeForm(defaultEmployee);
  }

  function logout() {
    setToken("");
    setUser(null);
    setSelectedEmployee(null);
    setActivePage("overview");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuthForm(authDefaults);
    setAuthMode("login");
  }

  if (!token) {
    return (
      <div className="marketing-shell">
        <header className="marketing-header">
          <a className="brand-link" href="/" aria-label="Orchard.io home">
            <span className="brand-icon" aria-hidden="true">
              <LogoIcon />
            </span>
            <span>Orchard.io</span>
          </a>
          <nav className="marketing-nav" aria-label="Primary navigation">
            <a href="#features">Features</a>
            <a href="#workflow">Workflow</a>
            <a href="#security">Security</a>
            <button className="login-link" type="button" onClick={() => openAuth("login")}>
              Sign in
            </button>
            <button className="trial-btn" type="button" onClick={() => openAuth("company")}>
              Create account
            </button>
          </nav>
        </header>

        <main className="marketing-main">
          <section className="hero-section">
            <div className="hero-copy">
              <p className="eyebrow">Directory management platform</p>
              <h1>Directory management for modern teams.</h1>
              <p className="hero-subtitle">
                One secure workspace for employee records, department visibility, leave requests,
                and payroll snapshots.
              </p>
              <div className="hero-actions">
                <button className="primary-btn hero-cta" type="button" onClick={() => openAuth("company")}>
                  Create company
                </button>
                <button className="ghost-btn hero-secondary" type="button" onClick={() => openAuth("login")}>
                  Sign in
                </button>
              </div>
              <div className="hero-metrics" aria-label="Platform metrics">
                {landingMetrics.map((metric) => (
                  <article key={metric.label} className="metric-pill">
                    <strong>{metric.value}</strong>
                    <span>{metric.label}</span>
                  </article>
                ))}
              </div>
            </div>

            <div className="hero-preview" aria-label="Orchard.io platform preview">
              <div className="preview-toolbar">
                <span className="window-dot red" />
                <span className="window-dot amber" />
                <span className="window-dot green" />
                <p>orchard.io/workspace</p>
              </div>
              <div className="preview-content">
                <section className="preview-snapshot">
                  <div>
                    <span className="preview-label">Directory health</span>
                    <strong>Live employee roster</strong>
                  </div>
                  <div className="preview-figure">
                    <strong>1,284</strong>
                    <span>employees</span>
                  </div>
                </section>
                <section className="preview-list">
                  {[
                    ["Aisha Khan", "Operations", "Available"],
                    ["Daniel Wu", "Finance", "Leave approved"],
                    ["Maya Sharma", "Product", "Payroll ready"],
                    ["Noah Patel", "Support", "Active"]
                  ].map(([name, dept, status]) => (
                    <article key={name} className="preview-row">
                      <div>
                        <strong>{name}</strong>
                        <span>{dept}</span>
                      </div>
                      <em>{status}</em>
                    </article>
                  ))}
                </section>
                <section className="preview-footer">
                  <div>
                    <span className="preview-label">Requests this week</span>
                    <strong>18 leave approvals</strong>
                  </div>
                  <div className="progress-meter" aria-hidden="true">
                    <span />
                  </div>
                </section>
              </div>
            </div>
          </section>

          <section className="feature-band" id="features">
            <div className="section-kicker">
              <p className="eyebrow">Features</p>
              <h2>Everything a real directory management system should do.</h2>
            </div>
            <div className="feature-grid" aria-label="Orchard.io platform features">
              {landingFeatures.map((feature) => (
                <article className="feature-card" key={feature.title}>
                  <span className="feature-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" role="img">
                      <path d={feature.icon} />
                    </svg>
                  </span>
                  <h3>{feature.title}</h3>
                  <p>{feature.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="workflow-band" id="workflow">
            <div className="section-kicker">
              <p className="eyebrow">Workflow</p>
              <h2>A simple path from signup to daily operations.</h2>
            </div>
            <div className="workflow-grid">
              {workflowSteps.map((step, index) => (
                <article className="workflow-card" key={step.title}>
                  <span className="workflow-index">0{index + 1}</span>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="security-band" id="security">
            <div>
              <p className="eyebrow">Security</p>
              <h2>Private records stay private by design.</h2>
            </div>
            <p>
              Company admins handle the company workspace, while employees only reach the records
              and actions meant for them.
            </p>
            <button className="primary-btn" type="button" onClick={() => openAuth("company")}>
              Start a workspace
            </button>
          </section>
        </main>

        <footer className="marketing-footer">
          <div>
            <strong>Orchard.io support</strong>
            <a href="mailto:support@orchard.io">support@orchard.io</a>
          </div>
          <p>Orchard.io keeps company records organized, searchable, and easy to govern.</p>
        </footer>

        {showAuthModal && (
          <div className="auth-modal-overlay" role="presentation" onClick={() => setShowAuthModal(false)}>
            <section
              className="auth-card"
              role="dialog"
              aria-modal="true"
              aria-labelledby="auth-title"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                className="auth-close"
                type="button"
                aria-label="Close sign in"
                onClick={() => setShowAuthModal(false)}
              >
                x
              </button>
              <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
                <button
                  type="button"
                  className={authMode === "login" ? "auth-tab active" : "auth-tab"}
                  onClick={() => {
                    setError("");
                    setAuthMode("login");
                  }}
                >
                  Sign in
                </button>
                <button
                  type="button"
                  className={authMode === "company" ? "auth-tab active" : "auth-tab"}
                  onClick={() => {
                    setError("");
                    setAuthMode("company");
                  }}
                >
                  Company admin
                </button>
                <button
                  type="button"
                  className={authMode === "employee" ? "auth-tab active" : "auth-tab"}
                  onClick={() => {
                    setError("");
                    setAuthMode("employee");
                  }}
                >
                  Employee
                </button>
              </div>
              <h2 id="auth-title">
                {authMode === "login"
                  ? "Sign in"
                  : authMode === "company"
                    ? "Create company admin account"
                    : "Create employee account"}
              </h2>
              <p className="muted">
                {authMode === "login"
                  ? "Enter your account details to continue."
                  : authMode === "company"
                    ? "Create a company admin account."
                    : "Use your workspace ID to create an employee account."}
              </p>
              <form onSubmit={handleAuthSubmit}>
                {authMode === "employee" && (
                  <label>
                    Workspace ID
                    <input
                      required
                      placeholder="00000000-0000-0000-0000-000000000000"
                      value={authForm.company_id}
                      onChange={(e) => setAuthForm({ ...authForm, company_id: e.target.value })}
                    />
                  </label>
                )}
                {authMode === "company" && (
                  <div className="form-row-2">
                    <label>
                      First name
                      <input
                        required
                        placeholder="Ava"
                        value={authForm.first_name}
                        onChange={(e) => setAuthForm({ ...authForm, first_name: e.target.value })}
                      />
                    </label>
                    <label>
                      Last name
                      <input
                        required
                        placeholder="Patel"
                        value={authForm.last_name}
                        onChange={(e) => setAuthForm({ ...authForm, last_name: e.target.value })}
                      />
                    </label>
                  </div>
                )}
                {authMode === "employee" && (
                  <div className="form-row-2">
                    <label>
                      First name
                      <input
                        required
                        placeholder="Maya"
                        value={authForm.first_name}
                        onChange={(e) => setAuthForm({ ...authForm, first_name: e.target.value })}
                      />
                    </label>
                    <label>
                      Last name
                      <input
                        required
                        placeholder="Sharma"
                        value={authForm.last_name}
                        onChange={(e) => setAuthForm({ ...authForm, last_name: e.target.value })}
                      />
                    </label>
                  </div>
                )}
                <label>
                  Email
                  <input
                    required
                    type="email"
                    placeholder={
                      authMode === "login"
                        ? "name@company.com"
                        : authMode === "company"
                          ? "admin@company.com"
                          : "employee@company.com"
                    }
                    value={authForm.email}
                    onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                  />
                </label>
                <label>
                  Password
                  <input
                    required
                    minLength={8}
                    placeholder="Password"
                    type="password"
                    value={authForm.password}
                    onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                  />
                </label>
                {authMode === "employee" && (
                  <p className="helper-copy">
                    Ask your company admin for the workspace ID before joining.
                  </p>
                )}
                <button type="submit" className="primary-btn">
                  {authMode === "login"
                    ? "Sign in"
                    : authMode === "company"
                      ? "Create admin account"
                      : "Create employee account"}
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => {
                    setError("");
                    setAuthMode(authMode === "login" ? "company" : "login");
                  }}
                >
                  {authMode === "login" ? "Need an account? Create one" : "Have an account? Sign in"}
                </button>
              </form>
              {error && <p className="error">{error}</p>}
            </section>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon-small">OI</span>
          <div>
            <strong>Orchard.io</strong>
            <p>Enterprise HRIS</p>
          </div>
        </div>
        <nav className="sidebar-nav">
          {user?.role === "SUPER_ADMIN" ? (
            <button
              className={activePage === "platform" ? "nav-item active" : "nav-item"}
              onClick={() => setActivePage("platform")}
            >
              Platform
            </button>
          ) : (
            <>
          {user?.role !== "EMPLOYEE" && (
            <button
              className={activePage === "overview" ? "nav-item active" : "nav-item"}
              onClick={() => setActivePage("overview")}
            >
              Overview
            </button>
          )}
          <button
            className={activePage === "directory" ? "nav-item active" : "nav-item"}
            onClick={() => setActivePage("directory")}
          >
            Directory
          </button>
          <button
            className={activePage === "leave" ? "nav-item active" : "nav-item"}
            onClick={() => setActivePage("leave")}
          >
            Leave
          </button>
          {isCompanyAdmin && (
            <button
              className={activePage === "payroll" ? "nav-item active" : "nav-item"}
              onClick={() => setActivePage("payroll")}
            >
              Payroll & Payments
            </button>
          )}
            </>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-profile-summary">
            <div className="user-avatar">{user?.email?.[0]?.toUpperCase() || "U"}</div>
            <div>
              <strong>{user?.email}</strong>
              <p>{roleLabel(user?.role)}</p>
            </div>
          </div>
          <button onClick={logout} className="logout-btn">
            Logout
          </button>
        </div>
      </aside>

      <main className="app-main-content">
        <header className="main-header">
          <h1>
            {activePage === "platform"
              ? "Platform Companies"
              : activePage === "overview"
              ? "Dashboard Overview"
              : activePage === "directory"
                ? "Employee Directory"
                : activePage === "leave"
                  ? "Leave Management"
                  : activePage === "payroll"
                    ? "Payroll & Payments"
                    : "Employee Details"}
          </h1>
          {canEdit && activePage === "directory" && (
            <button className="primary-btn" onClick={() => openModal()}>
              New Employee
            </button>
          )}
        </header>

        <div className="tab-pane-content">
          {activePage === "platform" && user?.role === "SUPER_ADMIN" ? (
            <section className="dashboard-grid">
              <article className="stat-card">
                <span>Companies</span>
                <h3>{platformCompanies.length}</h3>
                <p>tenant accounts on Orchard</p>
              </article>
              <article className="stat-card">
                <span>Active accounts</span>
                <h3>{platformCompanies.filter((company) => company.subscription_status === "ACTIVE").length}</h3>
                <p>currently allowed to use Orchard</p>
              </article>
              <article className="stat-card">
                <span>Payment due</span>
                <h3>{formatCurrency(platformCompanies.reduce((sum, company) => sum + Number(company.pending_amount || 0), 0))}</h3>
                <p>pending Orchard usage charges</p>
              </article>

              <div className="card-container col-span-2">
                <div className="card-header flex-header">
                  <div>
                    <h4 style={{ margin: 0 }}>Company account management</h4>
                    <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                      Superadmin can see company account and Orchard billing status only. Employee, leave, payroll, and salary data remain private inside each company.
                    </p>
                  </div>
                  <button className="ghost-btn" type="button" onClick={loadPlatformData}>
                    Refresh
                  </button>
                </div>
                {error && <p className="error">{error}</p>}
                <div className="table-responsive">
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>Company</th>
                        <th>Domain</th>
                        <th>Orchard status</th>
                        <th>Paid</th>
                        <th>Due</th>
                        <th>Failed</th>
                        <th>Latest billing</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading && (
                        <tr>
                          <td colSpan="8" className="text-center py-4">
                            Loading platform companies...
                          </td>
                        </tr>
                      )}
                      {!loading && !platformCompanies.length && (
                        <tr>
                          <td colSpan="8" className="text-center py-4">
                            No companies registered yet.
                          </td>
                        </tr>
                      )}
                      {!loading &&
                        platformCompanies.map((company) => (
                          <tr key={company.id}>
                            <td>
                              <strong>{company.company_name}</strong>
                              <p className="muted" style={{ margin: 0 }}>{company.id}</p>
                            </td>
                            <td>{company.domain || "No domain"}</td>
                            <td>
                              <span className={`status-badge ${statusClass(company.subscription_status)}`}>
                                {company.subscription_status}
                              </span>
                            </td>
                            <td>{formatCurrency(company.paid_amount)}</td>
                            <td>{formatCurrency(company.pending_amount)}</td>
                            <td>{formatCurrency(company.failed_amount)}</td>
                            <td>
                              {company.latest_billing_status ? (
                                <>
                                  <span className={`status-text-badge ${statusClass(company.latest_billing_status)}`}>
                                    {company.latest_billing_status}
                                  </span>
                                  <small>{new Date(company.latest_billing_date).toLocaleString()}</small>
                                </>
                              ) : (
                                "No billing yet"
                              )}
                            </td>
                            <td>
                              <button
                                className={company.subscription_status === "ACTIVE" ? "danger-btn" : "primary-btn-mini btn-success"}
                                type="button"
                                onClick={() => togglePlatformCompanyStatus(company.id)}
                              >
                                {company.subscription_status === "ACTIVE" ? "Suspend" : "Activate"}
                              </button>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card-container">
                <div className="card-header">
                  <h4>Record Orchard usage charge</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    Track platform subscription/payment status without exposing company employee data.
                  </p>
                </div>
                <form className="grid-form" onSubmit={recordOrchardBilling}>
                  <label>
                    Company
                    <select
                      required
                      value={platformBillingForm.company_id}
                      onChange={(e) => setPlatformBillingForm({ ...platformBillingForm, company_id: e.target.value })}
                    >
                      {platformCompanies.map((company) => (
                        <option key={company.id} value={company.id}>
                          {company.company_name} ({company.domain})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Amount
                    <input
                      required
                      type="number"
                      min="1"
                      step="0.01"
                      placeholder="25000"
                      value={platformBillingForm.amount}
                      onChange={(e) => setPlatformBillingForm({ ...platformBillingForm, amount: e.target.value })}
                    />
                  </label>
                  <label>
                    Status
                    <select
                      value={platformBillingForm.status}
                      onChange={(e) => setPlatformBillingForm({ ...platformBillingForm, status: e.target.value })}
                    >
                      <option value="PENDING">Pending</option>
                      <option value="PAID">Paid</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </label>
                  <button className="primary-btn" type="submit" disabled={!platformCompanies.length}>
                    Record usage charge
                  </button>
                </form>
              </div>

              <div className="card-container col-span-full">
                <div className="card-header">
                  <h4>Orchard billing ledger</h4>
                </div>
                <div className="recent-list-small">
                  {platformLedger.map((entry) => (
                    <div className="invoice-item" key={entry.id}>
                      <div>
                        <strong>{entry.company_name}</strong>
                        <p>{formatCurrency(entry.amount)} Orchard platform charge</p>
                      </div>
                      <div className="align-right">
                        <span className={`status-text-badge ${statusClass(entry.status)}`}>{entry.status}</span>
                        <small>{new Date(entry.billing_date).toLocaleString()}</small>
                      </div>
                    </div>
                  ))}
                  {!platformLedger.length && <p className="muted">No Orchard billing records yet.</p>}
                </div>
              </div>
            </section>
          ) : activePage === "overview" ? (
            <>
              <section className="stats-row">
                <article className="stat-card">
                  <span>Active records</span>
                  <h3>{total}</h3>
                  <p>employees tracked</p>
                </article>
                <article className="stat-card">
                  <span>Leave requests</span>
                  <h3>{leaveRequests.length}</h3>
                  <p>visible requests</p>
                </article>
                <article className="stat-card">
                  <span>Your role</span>
                  <h3>{roleLabel(user?.role)}</h3>
                  <p>permissions tier</p>
                </article>
              </section>

              <section className="card-container">
                <div className="card-header">
                  <h4>Leave & Payroll Overview</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    Quick signals: attendance health and payroll overhead.
                  </p>
                </div>

                <div className="overview-widgets">
                  <div className="widget ring-widget">
                    <div className="widget-head">
                      <span>Leave & Attendance Tracking</span>
                      <small>Company-wide</small>
                    </div>
                    <div className="ring-visual">
                      <svg viewBox="0 0 36 36" className="circular-chart blue">
                        <path className="circle-bg"
                          d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        <path 
                          className="circle" 
                          strokeDasharray={`${Math.min(100, Math.round(
                            (employees.reduce((acc, emp) => acc + (emp.leaves_taken || 0), 0) / 
                             Math.max(1, employees.reduce((acc, emp) => acc + (emp.leaves_allowed || 0), 0))) * 100
                          ))}, 100`} 
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <text x="18" y="20.35" className="percentage">
                          {employees.length 
                            ? `${Math.round(
                                (employees.reduce((acc, emp) => acc + (emp.leaves_taken || 0), 0) / 
                                 Math.max(1, employees.reduce((acc, emp) => acc + (emp.leaves_allowed || 0), 0))) * 100
                              )}%` 
                            : '—'}
                        </text>
                      </svg>
                      <div className="ring-meta">
                        <strong>{employees.length}</strong>
                        <small>tracked employees</small>
                      </div>
                    </div>
                  </div>

{canEdit && (
  <div className="widget payroll-widget">
    <div className="widget-head">
      <span>Payroll Overhead Summary</span>
      <small>Monthly estimate</small>
    </div>
    <div className="payroll-amount">
      <strong>
        {formatCurrency(employees.reduce((acc, emp) => acc + (Number(emp.base_salary) || 0), 0))}
      </strong>
      <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
        Active headcount: {employees.length}
      </p>
    </div>
  </div>
)}
                </div>
              </section>

              <section className="card-container">
                <div className="card-header">
                  <h4>Recently added</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    Latest employee entries from the directory.
                  </p>
                </div>
                <div className="recent-list">
                  {employees.slice(0, 5).map((employee) => (
                    <div key={employee.id} className="recent-item">
                      <div>
                        <strong>{employee.name}</strong>
                        <span>{employee.department}</span>
                      </div>
                      <button className="ghost-btn" onClick={() => viewEmployeeDetails(employee.id)}>
                        View Details
                      </button>
                    </div>
                  ))}
                  {!employees.length && <p className="muted">No recent employees yet.</p>}
                </div>
              </section>
            </>
          ) : activePage === "directory" ? (
            <>
              <section className="card-container">
                <div className="card-header flex-header">
                  <div>
                    <h4 style={{ margin: 0 }}>Directory List</h4>
                    <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                      Search, filter, and manage employee records.
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "16px", fontSize: "13px", color: "var(--text-muted)" }}>
                    <span>{visibleEmployees.length} records shown</span>
                    <span>•</span>
                    <span>{canEdit ? "salary visible" : "salary hidden"}</span>
                  </div>
                </div>

                <div className="directory-filters">
                  <input
                    className="search-input-field"
                    placeholder="Search by name or email"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setPage(1);
                    }}
                  />
                  <div className="filter-dropdowns">
                    <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                      <option value="name">Name</option>
                      <option value="email">Email</option>
                    </select>
                    <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
                      <option value="asc">Asc</option>
                      <option value="desc">Desc</option>
                    </select>
                    <button type="button" className="ghost-btn" onClick={clearDirectoryFilters}>
                      Clear filters
                    </button>
                  </div>
                </div>

                {error && <p className="error">{error}</p>}

                <div className="table-responsive">
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>ID</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Salary</th>
                        <th>Leave</th>
                        {canEdit && <th>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {loading && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="text-center py-4">
                            Loading employees...
                          </td>
                        </tr>
                      )}
                      {!loading && !visibleEmployees.length && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="text-center py-4">
                            No employees found for current filters.
                          </td>
                        </tr>
                      )}
                      {!loading &&
                        visibleEmployees.map((employee) => (
                          <tr key={employee.id}>
                            <td>
                              <button className="ghost-btn" style={{ padding: "4px 8px", fontSize: "13px" }} onClick={() => viewEmployeeDetails(employee.id)}>
                                {employee.name}
                              </button>
                            </td>
                            <td>{employee.employee_id}</td>
                            <td>{employee.email}</td>
                            <td><span className="role-pill">{roleLabel(employee.role)}</span></td>
                            <td>{canEdit ? formatCurrency(employee.base_salary) : "Hidden"}</td>
                            <td>{employee.leaves_taken ?? 0}/{employee.leaves_allowed ?? 24}</td>
                            {canEdit && (
                              <td>
                                <button className="ghost-btn" style={{ padding: "6px 12px", fontSize: "12px", marginRight: "8px" }} onClick={() => openModal(employee)}>
                                  Edit
                                </button>
                                <button className="danger-btn" style={{ padding: "6px 12px", fontSize: "12px" }} onClick={() => deleteEmployee(employee.id)}>
                                  Delete
                                </button>
                              </td>
                            )}
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>

                <div className="pagination-bar">
                  <span>
                    Page {page} / {Math.max(Math.ceil(total / 10), 1)}
                  </span>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button className="ghost-btn" disabled={page === 1} onClick={() => setPage(page - 1)}>
                      Prev
                    </button>
                    <button
                      className="ghost-btn"
                      disabled={page * 10 >= total}
                      onClick={() => setPage(page + 1)}
                    >
                      Next
                    </button>
                  </div>
                </div>
              </section>
            </>
          ) : activePage === "leave" ? (
            <section className="dashboard-grid">
              <div className="card-container">
                <div className="card-header">
                  <h4>{isCompanyAdmin ? "Company leave queue" : "Apply for leave"}</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    {isCompanyAdmin
                      ? "Review employee leave requests and update their status."
                      : "Submit a leave request and track approval status."}
                  </p>
                </div>
                {!isCompanyAdmin && (
                  <form className="grid-form" onSubmit={submitLeaveRequest}>
                    <label>
                      Start date
                      <input
                        required
                        type="date"
                        value={leaveForm.start_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                      />
                    </label>
                    <label>
                      End date
                      <input
                        required
                        type="date"
                        value={leaveForm.end_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                      />
                    </label>
                    <label>
                      Reason
                      <textarea
                        rows="4"
                        placeholder="Vacation, medical appointment, personal work..."
                        value={leaveForm.reason}
                        onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                      />
                    </label>
                    <button className="primary-btn" type="submit">
                      Apply leave
                    </button>
                  </form>
                )}
                {leaveBalance && (
                  <div className="overview-widgets">
                    <div className="widget">
                      <div className="widget-head">
                        <span>Leave balance</span>
                        <small>Available annual allowance</small>
                      </div>
                      <div className="payroll-amount">
                        <strong>{leaveBalance.available_balance}</strong>
                        <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: 0 }}>
                          {leaveBalance.leaves_taken} used of {leaveBalance.leaves_allowed}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="card-container col-span-2">
                <div className="card-header flex-header">
                  <div>
                    <h4 style={{ margin: 0 }}>{isCompanyAdmin ? "All leave requests" : "My leave status"}</h4>
                    <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                      Pending, approved, and rejected leave requests.
                    </p>
                  </div>
                  <button className="ghost-btn" type="button" onClick={loadLeaveData}>
                    Refresh
                  </button>
                </div>
                {error && <p className="error">{error}</p>}
                <div className="table-responsive">
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Dates</th>
                        <th>Reason</th>
                        <th>Status</th>
                        {isCompanyAdmin && <th>Action</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {loading && (
                        <tr>
                          <td colSpan={isCompanyAdmin ? 5 : 4} className="text-center py-4">
                            Loading leave requests...
                          </td>
                        </tr>
                      )}
                      {!loading && !leaveRequests.length && (
                        <tr>
                          <td colSpan={isCompanyAdmin ? 5 : 4} className="text-center py-4">
                            No leave requests yet.
                          </td>
                        </tr>
                      )}
                      {!loading &&
                        leaveRequests.map((request) => (
                          <tr key={request.id}>
                            <td>
                              <strong>{request.employee_name || user?.email}</strong>
                              <p className="muted" style={{ margin: 0 }}>{request.employee_email}</p>
                            </td>
                            <td>{request.start_date} to {request.end_date}</td>
                            <td>{request.reason || "No reason provided"}</td>
                            <td>
                              <span className={`status-badge ${statusClass(request.status)}`}>{request.status}</span>
                            </td>
                            {isCompanyAdmin && (
                              <td>
                                <button
                                  className="primary-btn-mini btn-success"
                                  type="button"
                                  onClick={() => approveLeaveRequest(request.id, "APPROVED")}
                                >
                                  Approve
                                </button>
                                <button
                                  className="primary-btn-mini btn-danger ml-2"
                                  type="button"
                                  onClick={() => approveLeaveRequest(request.id, "REJECTED")}
                                >
                                  Reject
                                </button>
                              </td>
                            )}
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          ) : activePage === "payroll" && isCompanyAdmin ? (
            <section className="dashboard-grid">
              <article className="stat-card">
                <span>Headcount</span>
                <h3>{payrollSummary?.headcount ?? employees.length}</h3>
                <p>employees on payroll</p>
              </article>
              <article className="stat-card">
                <span>Annual payroll</span>
                <h3>{formatCurrency(payrollSummary?.total_payroll_overhead)}</h3>
                <p>salary overhead</p>
              </article>
              <article className="stat-card">
                <span>Monthly estimate</span>
                <h3>{formatCurrency((payrollSummary?.total_payroll_overhead || 0) / 12)}</h3>
                <p>next payment cycle</p>
              </article>

              <div className="card-container col-span-2">
                <div className="card-header flex-header">
                  <div>
                    <h4 style={{ margin: 0 }}>Salary and payment schedule</h4>
                    <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                      Company admin view of employee compensation.
                    </p>
                  </div>
                  <button className="ghost-btn" type="button" onClick={loadPayrollData}>
                    Refresh
                  </button>
                </div>
                {error && <p className="error">{error}</p>}
                <div className="table-responsive">
                  <table className="modern-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Role</th>
                        <th>Annual salary</th>
                        <th>Payment day</th>
                        <th>Leave allowance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((employee) => (
                        <tr key={employee.id}>
                          <td>
                            <button className="ghost-btn" style={{ padding: "4px 8px", fontSize: "13px" }} onClick={() => viewEmployeeDetails(employee.id)}>
                              {employee.name}
                            </button>
                          </td>
                          <td><span className="role-pill">{roleLabel(employee.role)}</span></td>
                          <td>{formatCurrency(employee.base_salary)}</td>
                          <td>{employee.payment_date || 28}</td>
                          <td>{employee.leaves_allowed ?? 24} days</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card-container">
                <div className="card-header">
                  <h4>Record payment run</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    Simulate salary/payment processing for demo billing history.
                  </p>
                </div>
                <form className="grid-form" onSubmit={simulatePaymentRun}>
                  <label>
                    Amount
                    <input
                      required
                      type="number"
                      min="1"
                      step="0.01"
                      placeholder="85000"
                      value={paymentForm.amount}
                      onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                    />
                  </label>
                  <label>
                    Status
                    <select
                      value={paymentForm.status}
                      onChange={(e) => setPaymentForm({ ...paymentForm, status: e.target.value })}
                    >
                      <option value="PAID">Paid</option>
                      <option value="PENDING">Pending</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </label>
                  <button className="primary-btn" type="submit">
                    Record payment
                  </button>
                </form>
              </div>

              <div className="card-container col-span-full">
                <div className="card-header">
                  <h4>Payment ledger</h4>
                </div>
                <div className="recent-list-small">
                  {billingLedger.map((entry) => (
                    <div className="invoice-item" key={entry.id}>
                      <div>
                        <strong>{formatCurrency(entry.amount)}</strong>
                        <p>{entry.company_name} salary/payment event</p>
                      </div>
                      <div className="align-right">
                        <span className={`status-text-badge ${statusClass(entry.status)}`}>{entry.status}</span>
                        <small>{new Date(entry.billing_date).toLocaleString()}</small>
                      </div>
                    </div>
                  ))}
                  {!billingLedger.length && <p className="muted">No payment runs recorded yet.</p>}
                </div>
              </div>
            </section>
          ) : activePage === "details" && selectedEmployee ? (
            <section className="card-container max-width-700">
              <div className="card-header flex-header">
                <div>
                  <h4 style={{ margin: 0 }}>{selectedEmployee.name}</h4>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", margin: "4px 0 0" }}>
                    Employee ID: {selectedEmployee.employee_id}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  {canEdit && (
                    <button className="ghost-btn" onClick={() => openModal(selectedEmployee)}>
                      Edit Employee
                    </button>
                  )}
                  <button className="ghost-btn" onClick={() => setActivePage("directory")}>
                    Back to Directory
                  </button>
                </div>
              </div>
              <div className="profile-details-grid">
                <div className="detail-row">
                  <span className="label">Full Name</span>
                  <span className="value">{selectedEmployee.name}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Employee ID</span>
                  <span className="value">{selectedEmployee.employee_id}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Role</span>
                  <span className="value">{roleLabel(selectedEmployee.role)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Email</span>
                  <span className="value">{selectedEmployee.email}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Annual Salary</span>
                  <span className="value">{canEdit ? formatCurrency(selectedEmployee.base_salary) : "Hidden"}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Payment Day</span>
                  <span className="value">{selectedEmployee.payment_date || 28}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Leave Usage</span>
                  <span className="value">{selectedEmployee.leaves_taken ?? 0}/{selectedEmployee.leaves_allowed ?? 24}</span>
                </div>
              </div>
            </section>
          ) : null}
        </div>
      </main>

      {showModal && (
        <div className="modal-backdrop-overlay" onClick={closeModal}>
          <div className="modal-window-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-card-header">
              <h2>{editingEmployeeId ? "Update Employee" : "Add Employee"}</h2>
              <button className="modal-close-icon" onClick={closeModal}>
                &times;
              </button>
            </div>
            <form onSubmit={editingEmployeeId ? updateEmployee : createEmployee}>
              <div className="modal-card-body">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                  <label style={{ marginBottom: 0 }}>
                    First name
                    <input
                      required
                      placeholder="Maya"
                      value={employeeForm.first_name}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, first_name: e.target.value })}
                    />
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Last name
                    <input
                      required
                      placeholder="Sharma"
                      value={employeeForm.last_name}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, last_name: e.target.value })}
                    />
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Email
                    <input
                      required
                      type="email"
                      placeholder="employee@abc.com"
                      value={employeeForm.email}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, email: e.target.value })}
                    />
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Role
                    <select
                      value={employeeForm.role}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, role: e.target.value })}
                    >
                      <option value="EMPLOYEE">Employee</option>
                      <option value="COMPANY_ADMIN">Company admin</option>
                    </select>
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Annual salary
                    <input
                      required
                      type="number"
                      min="1"
                      placeholder="85000"
                      value={employeeForm.base_salary}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, base_salary: e.target.value })}
                    />
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Payment day
                    <input
                      required
                      type="number"
                      min="1"
                      max="31"
                      value={employeeForm.payment_date}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, payment_date: e.target.value })}
                    />
                  </label>
                  <label style={{ marginBottom: 0 }}>
                    Leave allowance
                    <input
                      required
                      type="number"
                      min="0"
                      value={employeeForm.leaves_allowed}
                      onChange={(e) => setEmployeeForm({ ...employeeForm, leaves_allowed: e.target.value })}
                    />
                  </label>
                </div>
              </div>
              <div className="modal-card-footer">
                <button type="button" className="ghost-btn" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn">
                  {editingEmployeeId ? "Save changes" : "Create employee"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
