// Catálogos con la misma organización del buscador de la Rama Judicial
// (https://publicacionesprocesales.ramajudicial.gov.co/): Departamento, Entidad, Especialidad y Despacho.

// Listas exactas del portal (sección «Filtros»), con sus códigos.
export const DEPARTAMENTOS = [
  "AMAZONAS",
  "ANTIOQUIA",
  "ARAUCA",
  "ATLÁNTICO",
  "BOGOTÁ",
  "BOLÍVAR",
  "BOYACÁ",
  "CALDAS",
  "CAQUETÁ",
  "CASANARE",
  "CAUCA",
  "CESAR",
  "CHOCÓ",
  "CUNDINAMARCA",
  "CÓRDOBA",
  "GUAINÍA",
  "GUAVIARE",
  "HUILA",
  "LA GUAJIRA",
  "MAGDALENA",
  "META",
  "NARIÑO",
  "NORTE DE SANTANDER",
  "PUTUMAYO",
  "QUINDÍO",
  "RISARALDA",
  "SAN ANDRÉS",
  "SANTANDER",
  "SUCRE",
  "TOLIMA",
  "VALLE DEL CAUCA",
  "VAUPÉS",
  "VICHADA",
];

export const ENTIDADES = [
  "CORTE SUPREMA DE JUSTICIA",
  "CONSEJO DE ESTADO",
  "CORTE CONSTITUCIONAL",
  "CONSEJO SUPERIOR DE LA JUDICATURA",
  "DIRECCION EJECUTIVA SECCIONAL DE ADMINISTRACION JUDICIAL DESAJ",
  "CONSEJO SECCIONAL",
  "TRIBUNAL SUPERIOR",
  "TRIBUNAL ADMINISTRATIVO",
  "COMISIÓN SECCIONAL DE DISCIPLINA JUDICIAL",
  "JUZGADO DE CIRCUITO",
  "JUZGADO ADMINISTRATIVO",
  "JUZGADO CIRCUITO DE EJECUCIÓN",
  "JUZGADO MUNICIPAL",
  "JUZGADO DE PEQUEÑAS CAUSAS",
  "JUZGADO MUNICIPAL DE EJECUCIÓN",
  "CENTRO DE SERVICIOS ADMINISTRATIVOS",
  "CENTRO DE SERVICIOS JUDICIALES",
];

export const ESPECIALIDADES = [
  "CONSTITUCIONAL",
  "ADMINISTRATIVA",
  "DISCIPLINARIA",
  "CIVIL",
  "PENAL",
  "LABORAL",
  "PENAL ESPECIALIZADO",
  "SALA ÚNICA",
  "PENAL CON FUNCIÓN DE CONOCIMIENTO",
  "FAMILIA",
  "CIVIL - LABORAL",
  "CIVIL - FAMILIA",
  "CIVIL - FAMILIA - LABORAL",
  "SECRETARÍA GENERAL",
  "PENAL PARA ADOLESCENTES CON FUNCIÓN DE CONOCIMIENTO",
  "PENAL JUSTICIA Y PAZ",
  "PENAL ESPECIALIZADOS DE EXTINCIÓN DE DOMINIO",
  "CIVIL RESTITUCIÓN DE TIERRAS",
  "SECCIÓN PRIMERA",
  "SECCIÓN SEGUNDA",
  "SECCIÓN TERCERA",
  "SECCIÓN CUARTA",
  "SIN SECCIÓN",
  "OFICINA JUDICIAL",
  "SIN SECCIÓN - ORAL",
  "SECCIÓN PRIMERA - ORAL",
  "SECCIÓN SEGUNDA - ORAL",
  "SECCIÓN TERCERA - ORAL",
  "SECCIÓN CUARTA - ORAL",
  "SECCIÓN ÚNICA MIXTA (ESCRIT-ORAL)",
  "SIN SECCIÓN - MIXTA",
  "SECCIÓN SEGUNDA MIXTA - ORAL",
  "SECCIÓN TERCERA MIXTA - ORAL",
  "PENAL MIXTO(LEYES 600, 906 Y 1098)",
  "CIVIL ORALIDAD",
  "FAMILIA ORALIDAD",
  "CENTRO DE SERVICIOS ADMINISTRATIVOS",
  "PENAL PARA ADOLESCENTES CON FUNCIÓN DE CONTROL DE GARANTÍAS",
  "CENTRO DE SERVICIOS JUDICIALES",
  "OFICINA DE SERVICIOS",
  "PROMISCUO DE FAMILIA",
  "EJECUCIÓN DE PENAS Y MEDIDAS DE SEGURIDAD",
  "PENAL CON FUNCIÓN DE CONTROL DE GARANTÍAS",
  "PROMISCUO / COMPETENCIA MÚLTIPLE",
  "CONSEJO SUPERIOR",
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
  "CIVIL RESTITUCIÓN DE TIERRAS": ["Restitución y formalización de tierras despojadas", "Proceso de restitución de tierras"],
};

export const todasLasClases = () => {
  const salida = [];
  for (const [especialidad, clases] of Object.entries(CLASES_PROCESO)) {
    for (const nombre of clases) salida.push({ value: nombre, label: nombre, grupo: especialidad });
  }
  return salida;
};

// Grupos de clases que corresponden a cada especialidad del portal.
export const gruposDeClases = (especialidad) => {
  const e = (especialidad || "").toUpperCase();
  if (!e) return Object.keys(CLASES_PROCESO);
  if (e === "CIVIL - FAMILIA - LABORAL" || e.startsWith("PROMISCUO / COMPETENCIA")) return ["CIVIL", "FAMILIA", "LABORAL"];
  if (e === "CIVIL - FAMILIA") return ["CIVIL", "FAMILIA"];
  if (e === "CIVIL - LABORAL") return ["CIVIL", "LABORAL"];
  if (e.includes("RESTITUCIÓN DE TIERRAS")) return ["CIVIL RESTITUCIÓN DE TIERRAS"];
  if (e.startsWith("CIVIL")) return ["CIVIL"];
  if (e.startsWith("FAMILIA") || e === "PROMISCUO DE FAMILIA") return ["FAMILIA"];
  if (e.startsWith("LABORAL")) return ["LABORAL"];
  if (e.startsWith("PENAL") || e.startsWith("EJECUCIÓN DE PENAS")) return ["PENAL"];
  if (e === "CONSTITUCIONAL") return ["CONSTITUCIONAL"];
  if (e === "ADMINISTRATIVA" || e.startsWith("SECCIÓN") || e.startsWith("SIN SECCIÓN")) return ["ADMINISTRATIVA"];
  return [];
};
