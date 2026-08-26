import Layout from "../components/Layout";

export default function Configuracion() {
  return (
    <Layout>
      <div style={{ minHeight: "100vh", background: "#f4f7fb", fontFamily: "sans-serif" }}>
        <header
          style={{
            background: "white",
            padding: "16px 32px",
            fontSize: "20px",
            fontWeight: "bold",
            borderBottom: "1px solid #e9edf2",
          }}
        >
          ⚙️ Configuración
        </header>
        <main style={{ padding: "32px" }}>
          <p>Próximamente: preferencias de cuenta, notificaciones y seguridad.</p>
        </main>
      </div>
    </Layout>
  );
}