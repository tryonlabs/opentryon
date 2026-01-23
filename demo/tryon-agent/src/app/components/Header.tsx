"use client";

import { Menu } from "lucide-react";
import Image from "next/image";

interface HeaderProps {
  onMenuToggle: () => void;
}

export default function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[var(--card-bg)] border-b border-[var(--border-primary)] shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6">
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Mobile menu toggle */}
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-primary)] transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded flex items-center justify-center overflow-hidden flex-shrink-0">
              <Image
                src="/tryon-labs-logo.png"
                alt="TryOn AI Logo"
                width={32}
                height={32}
                className="object-contain"
                priority
              />
            </div>
            <span className="text-sm sm:text-base font-medium text-[var(--text-primary)] whitespace-nowrap">
              TryOn AI
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
