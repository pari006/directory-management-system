const explicitApiBase = import.meta.env.VITE_API_BASE?.replace(/\/$/, "");
const apiBases = explicitApiBase
  ? [explicitApiBase]
  : [
      "http://127.0.0.1:8000/api/v1",
      "http://localhost:8000/api/v1",
      "http://127.0.0.1:8001/api/v1",
      "http://localhost:8001/api/v1",
      "/api/v1",
      "http://127.0.0.1:8000/api",
      "http://localhost:8000/api",
      "http://127.0.0.1:8001/api",
      "http://localhost:8001/api",
      "/api",
      ""
    ];
let lastWorkingBase = apiBases[0];

function formatValidationDetails(details) {
  if (!Array.isArray(details) || !details.length) return "";

  return details
    .map((detail) => {
      const path = Array.isArray(detail.loc)
        ? detail.loc.filter((part) => part !== "body" && part !== "query").join(".")
        : "";
      return path ? `${path}: ${detail.msg}` : detail.msg;
    })
    .join(" | ");
}

function formatApiError(body, status) {
  const validationMessage = formatValidationDetails(body.details || body.detail);
  return validationMessage || body.message || body.detail || `Request failed (${status})`;
}

function splitDisplayName(value = "") {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    return { first_name: "Employee", last_name: "User" };
  }

  const [firstName, ...lastParts] = parts;
  return {
    first_name: firstName,
    last_name: lastParts.join(" ") || "User"
  };
}

function toEmployeePayload(payload, { includeRole = true } = {}) {
  const employeePayload = {
    first_name: payload.first_name,
    last_name: payload.last_name,
    email: payload.email,
    base_salary: payload.base_salary ? Number(payload.base_salary) : undefined,
    payment_date: payload.payment_date ? Number(payload.payment_date) : undefined,
    leaves_allowed: payload.leaves_allowed ? Number(payload.leaves_allowed) : undefined
  };
  if (includeRole) {
    employeePayload.role = payload.role || "EMPLOYEE";
  } else if (payload.role) {
    employeePayload.role = payload.role;
  }
  return Object.fromEntries(
    Object.entries(employeePayload).filter(([, value]) => value !== undefined && value !== "")
  );
}

function normalizeEmployee(employee) {
  const fullName = [employee.first_name, employee.last_name].filter(Boolean).join(" ").trim();
  return {
    ...employee,
    name: fullName || employee.email,
    employee_id: employee.employee_id || String(employee.id || "").slice(0, 8),
    department: employee.department || "General",
    contact: employee.contact || employee.email,
    base_salary: employee.base_salary ?? null,
    payment_date: employee.payment_date ?? null,
    leaves_allowed: employee.leaves_allowed ?? null,
    leaves_taken: employee.leaves_taken ?? null
  };
}

function normalizeNetworkError(err, attemptedUrl) {
  if (err instanceof TypeError) {
    return new Error(
      `Unable to reach API at ${attemptedUrl}. Make sure the backend is running on port 8000 and that the /api path is available.`
    );
  }
  return err;
}

async function request(path, options = {}, token) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const bases = [lastWorkingBase, ...apiBases.filter((base) => base !== lastWorkingBase)];
  let lastError;

  for (const base of bases) {
    const url = `${base}${path}`;
    try {
      const response = await fetch(url, { ...options, headers });
      const contentType = response.headers.get("content-type") || "";
      const body = contentType.includes("application/json")
        ? await response.json()
        : { message: await response.text() };

      if (!response.ok) {
        const errMsg = formatApiError(body, response.status);
        const error = new Error(errMsg);
        error.status = response.status;
        error.url = url;
        if (response.status === 404 || response.status === 405) {
          lastError = error;
          continue;
        }
        throw error;
      }

      lastWorkingBase = base;
      return body;
    } catch (err) {
      if (err instanceof TypeError) {
        lastError = normalizeNetworkError(err, url);
        continue;
      }
      throw err;
    }
  }

  throw lastError || new Error("Request failed");
}

export const api = {
  signup: (payload, companyId) => {
    const query = companyId ? `?company_id=${encodeURIComponent(companyId)}` : "";
    return request(`/auth/signup${query}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  registerCompany: (payload) =>
    request("/auth/company/register", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  listEmployees: (params, token) => {
    const sortMap = {
      name: "first_name",
      employee_id: "first_name",
      department: "first_name",
      email: "email"
    };
    const backendParams = {
      ...params,
      sort_by: sortMap[params.sort_by] || params.sort_by || "first_name"
    };
    const query = new URLSearchParams(backendParams).toString();
    return request(`/employees?${query}`, {}, token).then((response) => ({
      ...response,
      data: {
        ...response.data,
        items: response.data.items.map(normalizeEmployee)
      }
    }));
  },
  getEmployee: (id, token) =>
    request(`/employees/${id}`, {}, token).then((response) => ({
      ...response,
      data: normalizeEmployee(response.data)
    })),
  createEmployee: (payload, token) =>
    request(
      "/employees",
      {
        method: "POST",
        body: JSON.stringify(toEmployeePayload(payload))
      },
      token
    ).then((response) => ({
      ...response,
      data: normalizeEmployee(response.data)
    })),
  updateEmployee: (id, payload, token) =>
    request(
      `/employees/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(toEmployeePayload(payload, { includeRole: false }))
      },
      token
    ).then((response) => ({
      ...response,
      data: normalizeEmployee(response.data)
    })),
  deleteEmployee: (id, token) =>
    request(
      `/employees/${id}`,
      {
        method: "DELETE"
      },
      token
    ),
  // Leaves
  requestLeave: (payload, token) =>
    request(
      "/leaves/request",
      {
        method: "POST",
        body: JSON.stringify(payload)
      },
      token
    ),
  approveLeave: (id, status, token) =>
    request(
      `/leaves/${id}/approve`,
      {
        method: "PATCH",
        body: JSON.stringify({ status })
      },
      token
    ),
  getMyLeaveRequests: (token) =>
    request("/leaves/my-requests", {}, token),
  getCompanyLeaveRequests: (token) =>
    request("/leaves/company", {}, token),
  getLeaveBalance: (employeeId, token) =>
    request(`/leaves/${employeeId}/balance`, {}, token),
  // Payroll
  getPayrollSummary: (token) =>
    request("/admin/payroll/summary", {}, token),
  getCompanyBillingLedger: (token) =>
    request("/billing/company/ledger", {}, token),
  simulateCompanyPayment: (payload, token) =>
    request(
      `/billing/company/simulate?amount=${encodeURIComponent(payload.amount)}&status=${encodeURIComponent(payload.status)}`,
      {
        method: "POST"
      },
      token
    ),
  // Platform admin
  listCompanies: (token) =>
    request("/superadmin/companies", {}, token),
  toggleCompanyStatus: (id, token) =>
    request(
      `/superadmin/companies/${id}/toggle-status`,
      {
        method: "POST"
      },
      token
    ),
  simulateBilling: (payload, token) =>
    request(
      `/billing/simulate?company_id=${encodeURIComponent(payload.company_id)}&amount=${payload.amount}&status=${payload.status}`,
      {
        method: "POST"
      },
      token
    ),
  getBillingLedger: (token) =>
    request("/billing/ledger", {}, token)
};
