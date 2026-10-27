// Catálogos con la misma organización del buscador de la Rama Judicial
// (https://publicacionesprocesales.ramajudicial.gov.co/): Departamento, Entidad, Especialidad y Despacho.

export const DEPARTAMENTOS = [
  "AMAZONAS", "ANTIOQUIA", "ARAUCA", "ATLÁNTICO", "BOGOTÁ, D.C.", "BOLÍVAR", "BOYACÁ", "CALDAS", "CAQUETÁ",
  "CASANARE", "CAUCA", "CESAR", "CHOCÓ", "CÓRDOBA", "CUNDINAMARCA", "GUAINÍA", "GUAVIARE", "HUILA", "LA GUAJIRA",
  "MAGDALENA", "META", "NARIÑO", "NORTE DE SANTANDER", "PUTUMAYO", "QUINDÍO", "RISARALDA",
  "SAN ANDRÉS Y PROVIDENCIA", "SANTANDER", "SUCRE", "TOLIMA", "VALLE DEL CAUCA", "VAUPÉS", "VICHADA",
];

export const ENTIDADES = [
  "CORTE SUPREMA DE JUSTICIA", "CONSEJO DE ESTADO", "CORTE CONSTITUCIONAL", "TRIBUNAL SUPERIOR",
  "TRIBUNAL ADMINISTRATIVO", "JUZGADO DE CIRCUITO", "JUZGADO MUNICIPAL", "JUZGADO ADMINISTRATIVO",
  "CENTRO DE SERVICIOS JUDICIALES", "OTROS JUZGADOS",
];

export const ESPECIALIDADES = [
  "CONSTITUCIONAL", "ADMINISTRATIVA", "DISCIPLINARIA", "CIVIL", "PENAL", "LABORAL", "FAMILIA", "CIVIL FAMILIA",
  "AGRARIA", "RESTITUCIÓN DE TIERRAS", "PEQUEÑAS CAUSAS Y COMPETENCIA MÚLTIPLE", "PROMISCUO / COMPETENCIA MÚLTIPLE",
];

// Clases de proceso agrupadas por especialidad (procesos que se tramitan con demanda).
export const CLASES_PROCESO = {
  CIVIL: [
    "Verbal de mayor cuantía", "Verbal de menor cuantía", "Verbal de mínima cuantía", "Verbal sumario",
    "Ejecutivo singular", "Ejecutivo con título hipotecario", "Ejecutivo con garantía real (prendaria)",
    "Monitorio", "Declaración de pertenencia", "Reivindicatorio", "Restitución de inmueble arrendado",
    "Divisorio", "Servidumbre", "Deslinde y amojonamiento", "Expropiación", "Pago por consignación",
    "Responsabilidad civil contractual", "Responsabilidad civil extracontractual", "Simulación",
    "Resolución de contrato", "Sucesión", "Aprehensión y entrega de garantía mobiliaria",
    "Insolvencia de persona natural no comerciante", "Jurisdicción voluntaria",
  ],
  LABORAL: [
    "Ordinario laboral de primera instancia", "Ordinario laboral de única instancia", "Ejecutivo laboral",
    "Fuero sindical", "Reconocimiento y pago de pensión", "Pensión de sobrevivientes",
    "Contrato realidad", "Cobro de aportes a seguridad social", "Calificación de suspensión o paro",
  ],
  FAMILIA: [
    "Fijación de cuota alimentaria", "Aumento, disminución o exoneración de cuota alimentaria",
    "Ejecutivo de alimentos", "Custodia y cuidado personal", "Regulación de visitas", "Divorcio",
    "Cesación de efectos civiles de matrimonio religioso", "Separación de cuerpos", "Separación de bienes",
    "Liquidación de sociedad conyugal", "Declaración de unión marital de hecho", "Investigación de paternidad",
    "Impugnación de paternidad", "Privación de patria potestad", "Adopción",
    "Adjudicación de apoyos", "Sucesión",
  ],
  ADMINISTRATIVA: [
    "Nulidad simple", "Nulidad y restablecimiento del derecho", "Reparación directa",
    "Controversias contractuales", "Ejecutivo", "Repetición", "Acción de cumplimiento",
    "Acción popular", "Acción de grupo",
  ],
  CONSTITUCIONAL: ["Acción de tutela", "Acción de cumplimiento", "Acción popular", "Acción de grupo", "Hábeas corpus"],
  PENAL: ["Incidente de reparación integral", "Acción civil dentro del proceso penal"],
  AGRARIA: ["Proceso agrario", "Pertenencia agraria", "Restitución de tierras"],
};

export const todasLasClases = () => {
  const salida = [];
  for (const [especialidad, clases] of Object.entries(CLASES_PROCESO)) {
    for (const nombre of clases) salida.push({ value: nombre, label: nombre, grupo: especialidad });
  }
  return salida;
};
