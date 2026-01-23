"use client";

import { useState, useEffect } from "react";
import * as React from "react";
import { Sidebar } from "react-pro-sidebar";
import { useTheme } from "../../components/ThemeProvider";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import {
  Home,
  ChevronDown,
  ChevronUp,
  Palette,
  ChevronsLeft,
  ChevronsRight,
  Sparkles,
  Shirt,
  MessageSquare,
  LucideIcon,
} from "lucide-react";
import ThemeToggle from "../../components/ThemeToggle";

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
}

export default function AppSidebar({ collapsed, setCollapsed }: SidebarProps) {
  const { theme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const [selected, setSelected] = useState("");
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const getInitials = (name?: string) => {
    if (!name) return "TA";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  useEffect(() => {
    // Set active state based on current pathname
    if (pathname === "/" || pathname === "/dashboard") {
      setSelected("home");
    } else if (pathname === "/fashion-prompt-builder") {
      setSelected("fashion-prompt-builder");
    } else if (pathname === "/virtual-tryon") {
      setSelected("virtual-tryon");
    }
  }, [pathname]);

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showProfileMenu && !target.closest('.profile-menu-container')) {
        setShowProfileMenu(false);
      }
    };

    if (showProfileMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showProfileMenu]);

  const [isMobile, setIsMobile] = useState(false);

  // Menu items configuration - 3 screens for tryon-agent
  const menuItems: { key: string; href: string; icon: LucideIcon; label: string }[] = [
    { key: "home", href: "/", icon: MessageSquare, label: "Dashboard" },
    { key: "fashion-prompt-builder", href: "/fashion-prompt-builder", icon: Sparkles, label: "Fashion Prompt Builder" },
    { key: "virtual-tryon", href: "/virtual-tryon", icon: Shirt, label: "Virtual Try-On" },
  ];

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  return (
    <Sidebar
      collapsed={collapsed}
      rootStyles={{
        backgroundColor: theme === "dark" ? "var(--bg-secondary)" : "var(--bg-tertiary)",
        borderRight: "1px solid var(--border-primary)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
      className={`fixed left-0 top-16 z-40 ${isMobile ? (collapsed ? 'mobile-sidebar-hidden' : 'mobile-sidebar-visible') : ''}`}
      style={{ 
        height: 'calc(100vh - 4rem)',
      }}
      breakPoint="md"
      onBreakPoint={(broken) => {
        // Auto-collapse on mobile breakpoint only
        if (broken) {
          setCollapsed(true);
        } else {
          // On desktop, ensure sidebar is open by default
          setCollapsed(false);
        }
      }}
      onBackdropClick={() => {
        // Close sidebar on backdrop click (mobile)
        if (isMobile) {
          setCollapsed(true);
        }
      }}
      transitionDuration={300}
    >
      {/* Content */}
      <div className="flex-1 overflow-y-auto flex flex-col min-h-0">
        {/* Header Section */}
        <div className="px-3 py-3 border-b border-[var(--border-primary)] md:mt-16 flex-shrink-0">
          <div className="flex items-center justify-between">
            {!collapsed && (
              <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider flex items-center">
                Dashboard
              </p>
            )}
            {/* Toggle Button */}
            <button
              onClick={() => setCollapsed(!collapsed)}
              className={`p-2 rounded-lg transition-all duration-200 cursor-pointer
                ${collapsed ? 'mx-auto' : 'shrink-0'}
                ${theme === "dark" 
                  ? "bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 active:bg-white/15" 
                  : "bg-black/5 border border-black/10 hover:bg-black/10 hover:border-black/15 active:bg-black/15"
                }`}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? (
                <ChevronsRight size={16} className="text-[var(--text-secondary)]" />
              ) : (
                <ChevronsLeft size={16} className="text-[var(--text-secondary)]" />
              )}
            </button>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-2 min-h-0 overflow-y-auto">
          <div className="space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.key}
                onClick={() => {
                  setSelected(item.key);
                  router.push(item.href);
                }}
                title={item.label}
                className={`w-full flex items-center gap-3 rounded-lg transition-all duration-200 cursor-pointer
                  ${collapsed ? 'justify-center p-3' : 'p-3'}
                  ${selected === item.key
                    ? theme === "dark"
                      ? "bg-white/10 text-white"
                      : "bg-black/10 text-black"
                    : theme === "dark"
                      ? "text-[var(--text-secondary)] hover:bg-white/5 hover:text-white"
                      : "text-[var(--text-secondary)] hover:bg-black/5 hover:text-black"
                  }`}
              >
                <item.icon size={18} className="flex-shrink-0" />
                {!collapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </button>
            ))}
          </div>
        </nav>
      </div>

      {/* Profile Section at Bottom */}
      <div className="border-t border-[var(--border-primary)] p-2 pb-2 profile-menu-container mt-auto flex-shrink-0">
        {collapsed ? (
          <div
            className="w-full p-2 rounded-lg flex items-center justify-center"
            title="Theme Toggle"
          >
            <ThemeToggle className="w-8 h-8" />
          </div>
        ) : (
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="w-full p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-colors flex items-center gap-3 cursor-pointer"
            >
              <div className="w-10 h-10 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
                <Image
                  src="/tryon-labs-logo.png"
                  alt="TryOn AI Logo"
                  width={40}
                  height={40}
                  className="object-contain"
                />
              </div>
              <div className="flex-1 text-left min-w-0">
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                  TryOn AI
                </p>
                <p className="text-xs text-[var(--text-secondary)] truncate">
                  AI Assistant
                </p>
              </div>
              {showProfileMenu ? (
                <ChevronUp size={16} className="text-[var(--text-secondary)] flex-shrink-0" />
              ) : (
                <ChevronDown size={16} className="text-[var(--text-secondary)] flex-shrink-0" />
              )}
            </button>

            {/* Profile Dropdown Menu */}
            {showProfileMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-[var(--card-bg)] border border-[var(--border-primary)] rounded-lg shadow-lg overflow-hidden z-50 min-w-[200px]">
                <div className="px-4 py-3 hover:bg-[var(--bg-secondary)] transition-colors border-b border-[var(--border-primary)]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Palette size={16} className="text-[var(--text-secondary)]" />
                      <span className="text-sm text-[var(--text-primary)]">Theme</span>
                    </div>
                    <ThemeToggle className="cursor-pointer" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Sidebar>
  );
}
