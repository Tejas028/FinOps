import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, AlertTriangle, TrendingUp, PieChart, Bell } from 'lucide-react';
import { getHealth } from '../../api/health';

export const Sidebar: React.FC = () => {
  const [health, setHealth] = useState<"ok" | "degraded" | "down" | "checking">("checking");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await getHealth();
        setHealth(res.status === "ok" ? "ok" : "degraded");
      } catch (e) {
        setHealth("down");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: "/", icon: <LayoutDashboard size={18} />, label: "Overview" },
    { to: "/anomalies", icon: <AlertTriangle size={18} />, label: "Anomalies" },
    { to: "/forecasts", icon: <TrendingUp size={18} />, label: "Forecasts" },
    { to: "/attribution", icon: <PieChart size={18} />, label: "Attribution" },
    { to: "/alerts", icon: <Bell size={18} />, label: "Alerts" },
  ];

  return (
    <div style={{
      width: '220px',
      height: '100vh',
      position: 'fixed',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ padding: '24px 16px', fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
        FinOps Intel
      </div>
      
      <nav style={{ flex: 1, padding: '0 8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => (
          <NavLink 
            key={item.to} 
            to={item.to}
            end={item.to === "/"}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 16px',
              color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              borderLeft: `2px solid ${isActive ? 'var(--accent)' : 'transparent'}`,
              textDecoration: 'none',
              fontSize: '14px',
              fontWeight: 500,
              transition: 'all 0.2s ease',
            })}
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '16px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          background: health === "ok" ? "var(--green)" : health === "degraded" ? "var(--accent)" : "#4B4B5C"
        }} />
        API Status
      </div>
    </div>
  );
};
