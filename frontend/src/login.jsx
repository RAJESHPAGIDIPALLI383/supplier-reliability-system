
import React, { useState } from "react";
import { ShieldCheck, Lock, Mail } from "lucide-react";
import { loginUser } from "./services/api.js";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const data = await loginUser(email, password);

      if (!data || !data.access_token || !data.user) {
        throw new Error("Invalid login response from server.");
      }

      console.log("Login successful:", data.user);

      onLogin(data.user);

    } catch (err) {
      console.error("Login error:", err.response?.data || err);

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Login failed. Please try again."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>

        <div className="login-logo">
          <ShieldCheck size={32} />
        </div>

        <h1>
          YottaFlex<span>.ai</span>
        </h1>

        <p>Data Quality Monitoring Platform</p>

        <label htmlFor="email">Email address</label>

        <div className="login-input">
          <Mail size={18} />

          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <label htmlFor="password">Password</label>

        <div className="login-input">
          <Lock size={18} />

          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="login-button"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>

        <small>
          Secure access · Role-based authentication
        </small>

      </form>
    </div>
  );
}
