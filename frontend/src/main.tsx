import { createRoot } from 'react-dom/client';
import { App } from './App';
import { AppProvider } from './store';

createRoot(document.getElementById('root')!).render(<AppProvider><App /></AppProvider>);
