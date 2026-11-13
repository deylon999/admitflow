import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { captureAuthLink } from './shared/authLink';
captureAuthLink();

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
