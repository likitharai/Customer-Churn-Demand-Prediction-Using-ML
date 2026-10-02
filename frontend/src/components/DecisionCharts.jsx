import React from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import '../decision-charts.css';

const COLORS = ['#ef745f', '#e3a93b', '#2d8f72', '#4d7ea8', '#875aa8'];
const tooltipStyle = { border: '1px solid #dfe7e3', borderRadius: 10, fontSize: 12 };

function ChartPanel({ eyebrow, title, note, children }) {
  return <article className="panel decision-chart">
    <div className="panel-head"><div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div>{note && <span className="live-pill">{note}</span>}</div>
    <div className="chart-stage">{children}</div>
  </article>;
}

function EmptyChart({ children }) {
  return <div className="chart-empty">{children}</div>;
}

export function AgentDecisionCharts({ riskRows = [], tasks = [] }) {
  const groups = [
    { name: 'High', value: riskRows.filter(row => ['High', 'Very High'].includes(row.risk_level)).length },
    { name: 'Medium', value: riskRows.filter(row => row.risk_level === 'Medium').length },
    { name: 'Low', value: riskRows.filter(row => row.risk_level === 'Low').length },
  ];
  const priorities = ['urgent', 'high', 'medium', 'low'].map(name => ({
    name: name[0].toUpperCase() + name.slice(1),
    Open: tasks.filter(task => task.priority === name && task.status !== 'completed').length,
  }));
  return <section className="decision-grid">
    <ChartPanel eyebrow="CUSTOMER PRIORITY" title="Risk distribution" note={`${riskRows.length} assigned`}>
      {riskRows.length ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={groups} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={3}>{groups.map((item, index) => <Cell key={item.name} fill={COLORS[index]}/>)}</Pie><Tooltip contentStyle={tooltipStyle}/><Legend/></PieChart></ResponsiveContainer> : <EmptyChart>No assigned customer risk data yet.</EmptyChart>}
    </ChartPanel>
    <ChartPanel eyebrow="TODAY'S WORK" title="Open tasks by priority" note={`${tasks.filter(task => task.status !== 'completed').length} open`}>
      <ResponsiveContainer width="100%" height="100%"><BarChart data={priorities} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" tickLine={false}/><YAxis allowDecimals={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="Open" fill="#2d8f72" radius={[6, 6, 0, 0]}/></BarChart></ResponsiveContainer>
    </ChartPanel>
  </section>;
}

export function ManagerDecisionCharts({ members = [], unassigned = 0, totalCustomers = 0 }) {
  const team = members.filter(member => member.role !== 'admin').map(member => ({
    name: member.full_name?.split(' ')[0] || member.email,
    Customers: member.assigned_customers || 0,
    Interactions: member.interactions || 0,
    Tasks: member.open_tasks || 0,
  }));
  const ownership = [
    { name: 'Assigned', value: Math.max(0, totalCustomers - unassigned) },
    { name: 'Unassigned', value: unassigned },
  ];
  return <section className="decision-grid manager-charts">
    <ChartPanel eyebrow="CAPACITY DECISION" title="Workload by team member" note={`${team.length} operators`}>
      {team.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={team} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" tickLine={false}/><YAxis allowDecimals={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle}/><Legend/><Bar dataKey="Customers" fill="#2d8f72" radius={[5, 5, 0, 0]}/><Bar dataKey="Interactions" fill="#4d7ea8" radius={[5, 5, 0, 0]}/><Bar dataKey="Tasks" fill="#e3a93b" radius={[5, 5, 0, 0]}/></BarChart></ResponsiveContainer> : <EmptyChart>Invite team members to compare workload.</EmptyChart>}
    </ChartPanel>
    <ChartPanel eyebrow="OWNERSHIP CONTROL" title="Customer assignment coverage" note={`${unassigned} unassigned`}>
      {totalCustomers ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={ownership} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={3}><Cell fill="#2d8f72"/><Cell fill="#ef745f"/></Pie><Tooltip contentStyle={tooltipStyle}/><Legend/></PieChart></ResponsiveContainer> : <EmptyChart>No customer ownership data yet.</EmptyChart>}
    </ChartPanel>
  </section>;
}

export function AdminDecisionCharts({ members = [], audits = [], models = [] }) {
  const roles = ['agent', 'manager', 'admin'].map((name, index) => ({
    name: name[0].toUpperCase() + name.slice(1),
    value: members.filter(member => member.role === name).length,
    color: COLORS[index + 2],
  }));
  const counts = audits.reduce((result, event) => {
    const name = String(event.action || 'other').replaceAll('.', ' ');
    result[name] = (result[name] || 0) + 1;
    return result;
  }, {});
  const activity = Object.entries(counts).map(([name, value]) => ({ name, Events: value })).sort((a, b) => b.Events - a.Events).slice(0, 6);
  const activeModels = models.filter(model => model.status === 'active').length;
  return <section className="decision-grid admin-charts">
    <ChartPanel eyebrow="ACCESS GOVERNANCE" title="Employees by role" note={`${members.length} seats`}>
      {members.length ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={roles} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={3}>{roles.map(role => <Cell key={role.name} fill={role.color}/>)}</Pie><Tooltip contentStyle={tooltipStyle}/><Legend/></PieChart></ResponsiveContainer> : <EmptyChart>No employees have joined yet.</EmptyChart>}
    </ChartPanel>
    <ChartPanel eyebrow="GOVERNANCE ACTIVITY" title="Most frequent audit events" note={`${audits.length} reviewed`}>
      {activity.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={activity} layout="vertical" margin={{ top: 4, right: 12, left: 22, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" allowDecimals={false}/><YAxis type="category" dataKey="name" width={105} tick={{ fontSize: 10 }}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="Events" fill="#4d7ea8" radius={[0, 6, 6, 0]}/></BarChart></ResponsiveContainer> : <EmptyChart>Governance activity will appear here.</EmptyChart>}
    </ChartPanel>
    <div className="model-health panel"><div><p className="eyebrow">MODEL GOVERNANCE</p><h3>Production model health</h3><p>Active models available to customer scoring.</p></div><strong>{activeModels}<small> active of {models.length}</small></strong></div>
  </section>;
}

