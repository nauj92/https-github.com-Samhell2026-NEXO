import { useEffect, useState } from "react";
import { Contact } from "lucide-react";
import api from "../api";
import Layout from "../components/Layout";
import NuevoCliente from "../components/NuevoCliente";
import { mensajeError } from "../utils/errores";
import { Encabezado, thStyle, tdStyle, enlace } from "../components/ui";

export default function Clientes() {
  const [lista, setLista] = useState([]);
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [editando, setEditando] = useState(undefined); // undefined = cerrado, null = nuevo, objeto = editar

  const cargar = () => {
    setCargando(true);
    api
      .get("/clientes/")
      .then((r) => setLista(r.data.results ?? r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar los clientes.")))
      .finally(() => setCargando(false));
  };
  useEffect(() => {
    cargar();
    api.get("/perfil/").then((r) => setPerfil(r.data)).catch(() => {});
  }, []);

  const eliminar = async (c) => {
    if (!window.confirm(`¿Eliminar al cliente "${c.nombre}"? Las demandas y expedientes que lo tengan asignado quedarán sin cliente.`)) return;
    setError(""); setAviso("");
    try {
      await api.delete(`/clientes/${c.id}/`);
      setAviso("Cliente eliminado.");
      cargar();
    } catch (err) {
      setError(mensajeError(err, "No se pudo eliminar el cliente."));
    }
  };

  const t = busqueda.toLowerCase();
  const visibles = lista.filter((c) => [c.nombre, c.numero_documento, c.email || "", c.telefono || ""].some((x) => x.toLowerCase().includes(t)));

  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <Encabezado Icono={Contact} titulo="Clientes" busqueda={busqueda} setBusqueda={setBusqueda} placeholder="Buscar cliente..." textoBoton="+ Nuevo cliente" onNuevo={() => setEditando(null)} />
        <main style={{ padding: "32px" }}>
          <p style={{ color: "#6b7f96", fontSize: "13px", marginTop: 0 }}>
            Los clientes que cree aquí aparecen para seleccionarlos al elaborar demandas, contestaciones y expedientes.
          </p>
          {error && <p style={{ color: "#c73a3a", background: "#fde8e8", padding: "8px 12px", borderRadius: "8px", whiteSpace: "pre-line" }}>{error}</p>}
          {aviso && <p style={{ color: "#1d6b3a", background: "#e6f6ec", padding: "8px 12px", borderRadius: "8px" }}>{aviso}</p>}
          {cargando ? <p>Cargando...</p> : (
            <div style={{ background: "white", borderRadius: "16px", border: "1px solid #eef2f6", overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    {["Nombre", "Documento", "Teléfono", "Correo", "Dirección", "Acción"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {visibles.map((c) => (
                    <tr key={c.id} style={{ borderTop: "1px solid #f0f3f8" }}>
                      <td style={tdStyle}><strong>{c.nombre}</strong></td>
                      <td style={tdStyle}>{c.tipo_documento} {c.numero_documento}</td>
                      <td style={tdStyle}>{c.telefono || "—"}</td>
                      <td style={tdStyle}>{c.email || "—"}</td>
                      <td style={tdStyle}>{c.direccion || "—"}</td>
                      <td style={tdStyle}>
                        <button style={enlace("#a8681a")} onClick={() => setEditando(c)}>Editar</button>
                        {perfil?.es_directivo && <button style={enlace("#c73a3a")} onClick={() => eliminar(c)}>Eliminar</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {visibles.length === 0 && <p style={{ padding: "24px", color: "#6b7f96" }}>{lista.length === 0 ? "Aún no hay clientes. Use «+ Nuevo cliente» para crear el primero." : "No hay clientes que coincidan."}</p>}
            </div>
          )}
        </main>
        {editando !== undefined && (
          <NuevoCliente
            cliente={editando || undefined}
            onClose={() => setEditando(undefined)}
            onGuardado={() => { setAviso(editando ? "Cliente actualizado." : "Cliente creado."); setEditando(undefined); cargar(); }}
          />
        )}
      </div>
    </Layout>
  );
}
