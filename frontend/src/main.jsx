import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { aplicarTema, temaGuardado } from './utils/tema'

// Aplica el modo guardado antes de dibujar, para que no parpadee
aplicarTema(temaGuardado())

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
