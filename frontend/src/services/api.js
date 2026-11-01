
import axios from "axios";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const API = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// Attach token to authenticated requests
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("yotta_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Preserve the original Axios error and response
API.interceptors.response.use(
  (response) => response,
  (error) => {
    error.message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Something went wrong. Please try again.";

    return Promise.reject(error);
  }
);

// Login
export const loginUser = async (email, password) => {
  const response = await API.post("/auth/login", {
    email: email.trim().toLowerCase(),
    password,
  });

  const data = response.data;

  if (data.access_token) {
    localStorage.setItem("yotta_token", data.access_token);
  }

  if (data.user) {
    localStorage.setItem("yotta_user", JSON.stringify(data.user));
  }

  return data;
};

export const getProfile = async () => {
  const response = await API.get("/auth/me");
  return response.data;
};

export const getSuppliers = async () => {
  const response = await API.get("/suppliers");
  return response.data;
};

export const getScores = async () => {
  const response = await API.get("/scores");
  return response.data;
};

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await API.post("/upload/csv", formData);
  return response.data;
};

export const runPipeline = async (filename) => {
  const response = await API.post("/upload/pipeline/run", null, {
    params: { filename },
  });

  return response.data;
};

export const getPipelineHistory = async (limit = 100) => {
  const response = await API.get("/upload/pipeline/history", {
    params: { limit },
  });

  return response.data;
};

export const getPipelineRunDetails = async (runId) => {
  if (!runId) throw new Error("Pipeline Run ID is missing.");

  const response = await API.get(
    `/upload/pipeline/history/${encodeURIComponent(runId)}`
  );

  return response.data;
};

export const downloadPipelineReport = async (runId, reportType) => {
  if (!runId) throw new Error("Pipeline Run ID is missing.");

  if (!["valid", "rejected"].includes(reportType)) {
    throw new Error("Invalid report type.");
  }

  const response = await API.get(
    `/upload/pipeline/report/${encodeURIComponent(runId)}/${reportType}`,
    { responseType: "blob" }
  );

  return response.data;
};

export const logoutUser = () => {
  localStorage.removeItem("yotta_token");
  localStorage.removeItem("yotta_user");
};

export default API;
