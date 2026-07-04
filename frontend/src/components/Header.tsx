'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navLinks = [
  { href: '/', label: 'Extract' },
  { href: '/leads', label: 'Leads' },
  { href: '/pricing', label: 'Pricing' },
];

export default function Header() {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  }

  return (
    <nav className="flex w-full items-center justify-between px-6 py-3 sticky top-0 z-50"
      style={{
        background: 'rgba(5,10,20,0.8)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(226,232,240,0.06)',
      }}
    >
      <Link href="/" className="flex items-center gap-2.5 no-underline text-[#F8FAFC] font-bold text-lg transition-transform hover:scale-[1.03]">
        <div className="w-9 h-9 rounded-[10px] flex items-center justify-center text-lg font-extrabold text-white shrink-0"
          style={{ background: 'linear-gradient(135deg, #0A4FD9, #00E5FF)' }}
        >
          S
        </div>
        <span>Scraven</span>
      </Link>

      <div className="flex items-center gap-3">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="no-underline text-sm px-3.5 py-2 rounded-lg transition-all"
            style={{
              color: isActive(link.href) ? '#F8FAFC' : '#94A3B8',
              background: isActive(link.href) ? 'rgba(148,163,184,0.08)' : 'transparent',
              fontWeight: isActive(link.href) ? 600 : 400,
            }}
            onMouseEnter={(e) => { if (!isActive(link.href)) { e.currentTarget.style.color = '#F8FAFC'; e.currentTarget.style.background = 'rgba(148,163,184,0.08)'; } }}
            onMouseLeave={(e) => { if (!isActive(link.href)) { e.currentTarget.style.color = '#94A3B8'; e.currentTarget.style.background = 'transparent'; } }}
          >
            {link.label}
          </Link>
        ))}

        <a href="/login"
          className="no-underline text-sm font-semibold px-4 py-2 rounded-lg text-white"
          style={{
            background: 'linear-gradient(135deg, #0A4FD9, #00E5FF)',
            opacity: 0.9,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = '1'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '0.9'; }}
        >
          Sign In
        </a>
      </div>
    </nav>
  );
}
