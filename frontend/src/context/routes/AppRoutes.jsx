import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import ExecutiveDashboard from '../pages/ExecutiveDashboard';
import CustomerAnalytics from '../pages/CustomerAnalytics';
import Prediction from '../pages/Prediction';
import RevenueRisk from '../pages/RevenueRisk';
import Recommendations from '../pages/Recommendations';
import SHAPAnalysis from '../pages/SHAPAnalysis';
import WhatIfAnalysis from '../pages/WhatIfAnalysis';
import SQLInsights from '../pages/SQLInsights';
import About from '../pages/About';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/executive" element={<ExecutiveDashboard />} />
      <Route path="/customers" element={<CustomerAnalytics />} />
      <Route path="/prediction" element={<Prediction />} />
      <Route path="/revenue" element={<RevenueRisk />} />
      <Route path="/recommendations" element={<Recommendations />} />
      <Route path="/shap" element={<SHAPAnalysis />} />
      <Route path="/whatif" element={<WhatIfAnalysis />} />
      <Route path="/sql" element={<SQLInsights />} />
      <Route path="/about" element={<About />} />
    </Routes>
  );
}
