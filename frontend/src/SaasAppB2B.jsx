import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthProvider';
import WorkspaceLayoutLive from './components/WorkspaceLayoutLive';
import AuthB2B from './pages/AuthB2B';
import { CustomerProfile, Overview, Playbooks, RiskQueue } from './pages/OperationsB2B';
import { InteractionsWorkflow, TasksWorkflow } from './pages/RetentionWorkflow';
import CustomersAssignable from './pages/CustomersAssignable';
import ImportsAutomated from './pages/ImportsAutomated';
import { AdminDashboard, ManagerDashboard } from './pages/RoleDashboards';


function Protected() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen"><span className="brand-mark">R</span><p>Preparing workspace...</p></div>;
  return user ? <WorkspaceLayoutLive/> : <Navigate to="/login" replace/>;
}


export default function SaasAppB2B() {
  return <BrowserRouter><AuthProvider><Routes>
    <Route path="/login" element={<AuthB2B/>}/>
    <Route element={<Protected/>}>
      <Route index element={<Overview/>}/>
      <Route path="risk" element={<RiskQueue/>}/>
      <Route path="customers" element={<CustomersAssignable/>}/>
      <Route path="customers/:id" element={<CustomerProfile/>}/>
      <Route path="interactions" element={<InteractionsWorkflow/>}/>
      <Route path="tasks" element={<TasksWorkflow/>}/>
      <Route path="playbooks" element={<Playbooks/>}/>
      <Route path="manager" element={<ManagerDashboard/>}/>
      <Route path="imports" element={<ImportsAutomated/>}/>
      <Route path="admin" element={<AdminDashboard/>}/>
    </Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></AuthProvider></BrowserRouter>;
}


