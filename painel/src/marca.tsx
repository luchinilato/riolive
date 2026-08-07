/* Entry só de dev da página de prova da marca — servida em /marca.html.
   O build de produção continua entrando apenas por index.html. */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './tokens.css'
import { MarcaDemo } from './componentes/MarcaDemo'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MarcaDemo />
  </StrictMode>,
)
