'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

interface AppShellProps {
  children: ReactNode;
}

const mainNav = [
  { href: '/', label: 'Discover', icon: '⌂' },
  { href: '/search', label: '책 등록', icon: '⌕' },
  { href: '/log', label: '내 서재', icon: '✎' },
  { href: '/bookshelf', label: 'Download', icon: '⬇' },
  { href: '/scan', label: 'Favorite', icon: '⌁' }
];

const supportNav = [
  { href: '/', label: 'Setting', icon: '⚙' },
  { href: '/', label: 'Help', icon: 'i' },
  { href: '/', label: 'Log out', icon: '↩' }
];

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">THE BOOKS</div>

        <div className="nav-section-title">MENU</div>
        <nav className="nav-group">
          {mainNav.map((item) => (
            <Link key={item.label} href={item.href} className={`nav-item ${isActive(item.href) ? 'active' : ''}`}>
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <nav className="nav-group muted-group">
          {supportNav.map((item) => (
            <Link key={item.label} href={item.href} className="nav-item">
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-badge">
          <div className="badge-art" />
          <div className="badge-title">BOOK LIBRARY</div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="profile-chip">
            <div className="avatar-dot" />
            <span>Davis Workman</span>
          </div>
          <button className="bell-btn" type="button" aria-label="notification">
            ●
          </button>
        </header>

        <main className="page-wrap">{children}</main>
      </div>
    </div>
  );
}
