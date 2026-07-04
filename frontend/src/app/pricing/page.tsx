'use client';

import { useState } from 'react';

export default function PricingPage() {
  const [billing, setBilling] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <header className="text-center mb-12">
        <h1 className="gradient-text text-4xl font-extrabold mb-3">Simple, transparent pricing</h1>
        <p className="text-[#94A3B8] text-base leading-relaxed">
          Choose the plan that fits your lead generation needs. No hidden fees.
        </p>
      </header>

      <div className="flex items-center justify-center gap-3 mb-10">
        <button
          onClick={() => setBilling('monthly')}
          className="px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer"
          style={{
            background: billing === 'monthly' ? 'linear-gradient(135deg,#0A4FD9,#00E5FF)' : '#0E1825',
            color: billing === 'monthly' ? '#fff' : '#94A3B8',
            border: billing === 'monthly' ? 'none' : '1px solid rgba(226,232,240,0.08)',
          }}
        >
          Monthly
        </button>
        <button
          onClick={() => setBilling('yearly')}
          className="px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer"
          style={{
            background: billing === 'yearly' ? 'linear-gradient(135deg,#0A4FD9,#00E5FF)' : '#0E1825',
            color: billing === 'yearly' ? '#fff' : '#94A3B8',
            border: billing === 'yearly' ? 'none' : '1px solid rgba(226,232,240,0.08)',
          }}
        >
          Yearly <span className="text-[#00E5FF] text-xs">Save 20%</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-[400px] md:max-w-none mx-auto">
        {/* Guest */}
        <div className="bg-[rgba(14,24,37,0.95)] border border-[rgba(226,232,240,0.08)] rounded-2xl p-8 pt-8 flex flex-col transition-all hover:border-[rgba(0,229,255,0.2)] hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(0,229,255,0.08)]">
          <div className="text-xs font-semibold text-[#00E5FF] uppercase tracking-widest mb-2">Guest</div>
          <div className="text-4xl font-extrabold text-[#F8FAFC] mb-1">Free</div>
          <div className="text-sm text-[#94A3B8] mb-6 leading-relaxed">Try before you commit</div>
          <ul className="flex-1 space-y-0 mb-7">
            {[
              ['10 lifetime leads', true],
              ['Facebook & Instagram extraction', true],
              ['No history saved', false],
              ['No export', false],
              ['No inline editing', false],
            ].map(([text, check]) => (
              <li key={text as string} className="flex items-start gap-2.5 py-2 text-sm text-[#CBD5E1] border-b border-[rgba(226,232,240,0.04)] last:border-0">
                <CheckIcon ok={check as boolean} />
                {text as string}
              </li>
            ))}
          </ul>
          <a href="/register" className="block text-center py-3 rounded-xl text-sm font-semibold no-underline transition-all"
            style={{ background: 'rgba(148,163,184,0.08)', color: '#F8FAFC', border: '1px solid rgba(226,232,240,0.1)' }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(148,163,184,0.15)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(148,163,184,0.08)'; }}
          >
            Get Started
          </a>
        </div>

        {/* Free (popular) */}
        <div className="bg-[rgba(14,24,37,0.95)] border-2 border-[#00E5FF] rounded-2xl p-8 pt-8 flex flex-col relative transition-all hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(0,229,255,0.08)]">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#0A4FD9] to-[#00E5FF] text-white text-xs font-bold px-4 py-1 rounded-full uppercase tracking-wider">Most Popular</div>
          <div className="text-xs font-semibold text-[#00E5FF] uppercase tracking-widest mb-2">Free</div>
          <div className="text-4xl font-extrabold text-[#F8FAFC] mb-1">$0</div>
          <div className="text-sm text-[#94A3B8] mb-6 leading-relaxed">For individual users</div>
          <ul className="flex-1 space-y-0 mb-7">
            {[
              ['20 lifetime leads', true],
              ['Facebook & Instagram extraction', true],
              ['Full history saved', true],
              ['Export (XLSX, PDF, TXT, MD)', true],
              ['Inline lead editing', true],
              ['Bulk extraction', false],
              ['LinkedIn extraction', false],
              ['Priority support', false],
            ].map(([text, check]) => (
              <li key={text as string} className="flex items-start gap-2.5 py-2 text-sm text-[#CBD5E1] border-b border-[rgba(226,232,240,0.04)] last:border-0">
                <CheckIcon ok={check as boolean} />
                {text as string}
              </li>
            ))}
          </ul>
          <a href="/register" className="block text-center py-3 rounded-xl text-sm font-semibold no-underline text-white transition-all"
            style={{ background: 'linear-gradient(135deg, #0A4FD9, #00E5FF)' }}
            onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,229,255,0.25)'; }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; }}
          >
            Sign Up Free
          </a>
        </div>

        {/* Pro */}
        <div className="bg-[rgba(14,24,37,0.95)] border border-[rgba(226,232,240,0.08)] rounded-2xl p-8 pt-8 flex flex-col transition-all hover:border-[rgba(0,229,255,0.2)] hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(0,229,255,0.08)]">
          <div className="text-xs font-semibold text-[#00E5FF] uppercase tracking-widest mb-2">Pro</div>
          <div className="text-4xl font-extrabold text-[#F8FAFC] mb-1">
            {billing === 'monthly' ? '$9' : '$89'}
            <span className="text-base font-normal text-[#64748B]">/{billing === 'monthly' ? 'mo' : 'yr'}</span>
          </div>
          <div className="text-sm text-[#94A3B8] mb-6 leading-relaxed">
            {billing === 'monthly' ? 'For professionals and teams' : '$7.42/mo billed annually — save 20%'}
          </div>
          <ul className="flex-1 space-y-0 mb-7">
            {[
              ['Unlimited leads', true],
              ['Facebook, Instagram & LinkedIn extraction', true],
              ['Full history + advanced search', true],
              ['Export all formats', true],
              ['Bulk extraction mode', true],
              ['Inline editing + status tracking', true],
              ['Priority support', true],
              ['Cancel anytime', true],
            ].map(([text, check]) => (
              <li key={text as string} className="flex items-start gap-2.5 py-2 text-sm text-[#CBD5E1] border-b border-[rgba(226,232,240,0.04)] last:border-0">
                <CheckIcon ok={check as boolean} />
                {text as string}
              </li>
            ))}
          </ul>
          <button
            onClick={() => {
              const token = localStorage.getItem('skarbol_token');
              if (!token) { window.location.href = '/register?plan=pro'; return; }
              alert('Pro subscription is coming soon! You will be able to upgrade via bKash, Nagad, or card payment.');
            }}
            className="block w-full text-center py-3 rounded-xl text-sm font-semibold text-white transition-all cursor-pointer border-none"
            style={{ background: 'linear-gradient(135deg, #0A4FD9, #00E5FF)' }}
            onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,229,255,0.25)'; }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; }}
          >
            Upgrade to Pro
          </a>
        </div>
      </div>

      {/* FAQ */}
      <div className="mt-16 max-w-lg mx-auto">
        <h2 className="text-center text-2xl font-bold mb-8 text-[#F8FAFC]">Frequently asked questions</h2>
        {[
          ['What counts as a lead?', 'Each business profile you extract and save counts as one lead. Duplicates are detected automatically and don\'t count toward your limit.'],
          ['Can I upgrade from Free to Pro?', 'Yes, you can upgrade at any time. Your existing leads carry over and you get instant access to unlimited extraction and all Pro features.'],
          ['What payment methods do you accept?', 'We accept Visa, Mastercard, bKash, and Nagad. Bangladeshi users can pay in BDT (1499 BDT/month). Enterprise invoicing is available on request.'],
          ['Is there a free trial for Pro?', 'Sign up for the Free plan to explore the tool with 20 lifetime leads. Upgrade to Pro when you\'re ready for unlimited access.'],
        ].map(([q, a]) => (
          <FaqItem key={q as string} question={q as string} answer={a as string} />
        ))}
      </div>
    </div>
  );
}

function CheckIcon({ ok }: { ok: boolean }) {
  return ok
    ? <svg className="w-4 h-4 shrink-0 mt-0.5 text-[#00E5FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 6L9 17l-5-5"/></svg>
    : <svg className="w-4 h-4 shrink-0 mt-0.5 text-[#475569]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>;
}

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-[rgba(226,232,240,0.06)] py-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex justify-between items-center w-full text-left text-[#E2E8F0] text-sm font-medium py-1 cursor-pointer bg-transparent border-none"
      >
        {question}
        <svg className={`w-5 h-5 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
      </button>
      {open && <div className="text-[#94A3B8] text-sm leading-relaxed pt-2">{answer}</div>}
    </div>
  );
}
