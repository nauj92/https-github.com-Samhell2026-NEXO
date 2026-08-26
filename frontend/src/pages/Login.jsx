import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const response = await api.post("/token/", { username, password });
      localStorage.setItem("access_token", response.data.access);
      localStorage.setItem("refresh_token", response.data.refresh);
      navigate("/dashboard");
    } catch (err) {
      setError("Usuario o contraseña incorrectos.");
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", alignItems: "center", justifyContent: "center", background: "#0a1a2b" }}>
      <form onSubmit={handleSubmit} style={{ background: "white", padding: "40px", borderRadius: "16px", width: "320px" }}>
        <h2 style={{ marginBottom: "24px", color: "#0a1a2b" }}>⚖️ ERP</h2>
        {error && <p style={{ color: "#c73a3a", fontSize: "14px" }}>{error}</p>}
        <div style={{ marginBottom: "16px" }}>
          <label>Usuario</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", padding: "8px", marginTop: "4px" }}
          />
        </div>
        <div style={{ marginBottom: "24px" }}>
          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: "8px", marginTop: "4px" }}
          />
        </div>
        <button type="submit" style={{ width: "100%", padding: "10px", background: "#0a1a2b", color: "white", border: "none", borderRadius: "8px" }}>
          Ingresar
        </button>
      </form>
    </div>
  );
}