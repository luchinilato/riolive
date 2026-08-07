import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './tokens.css'
import './index.css'
import App from './App.tsx'
import { Barreira } from './componentes/Barreira'

const cliente = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <Barreira>
        <App />
      </Barreira>
    </QueryClientProvider>
  </StrictMode>,
)
