import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import Navbar from './components/Navbar/Navbar';
import Sidebar from './components/Sidebar/Sidebar';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />
        <div className="app-body">
          <Sidebar />
          <main className="app-main">
            <AppRoutes />
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
