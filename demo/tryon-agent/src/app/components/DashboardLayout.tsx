"use client";

import { useState, useEffect } from "react";
import AppSidebar from "./Sidebar";
import Header from "./Header";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // Auto-collapse only on mobile, keep desktop open
      if (mobile) {
        setCollapsed(true);
      } else {
        // Ensure desktop starts with sidebar open
        setCollapsed(false);
      }
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleToggle = () => {
    setCollapsed(!collapsed);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)] transition-colors">
      {/* Mobile backdrop */}
      {!collapsed && isMobile && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden"
          style={{ zIndex: 35 }}
          onClick={() => setCollapsed(true)}
        />
      )}
      
      <AppSidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      
      <Header onMenuToggle={handleToggle} />

      <div
        className="flex-1 transition-all duration-300 ease-in-out overflow-hidden flex flex-col"
        style={{
          marginLeft: isMobile ? "0" : collapsed ? "80px" : "80px",
          paddingTop: isMobile ? "64px" : "64px",
          height: isMobile ? 'calc(100vh - 64px)' : 'calc(100vh - 64px)',
        }}
      >
        {/* Main Content */}
        <main 
          className={`flex-1 overflow-y-auto overflow-x-hidden w-full transition-all duration-300 ease-in-out ${
            isMobile ? "pl-2 md:pl-4 pr-2 md:pr-4" : collapsed ? "pl-2 md:pl-3 pr-2 md:pr-3" : "pl-0 pr-0"
          }`}
          style={{ backgroundColor: 'var(--background)' }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
