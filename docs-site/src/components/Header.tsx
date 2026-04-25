import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { GITHUB_REPO_URL } from '@/config/public';
import searchIndex from '@/content/search-index.json';
import zh from '@/locales/zh-CN.json';
import './Header.css';

interface HeaderProps {
  onMenuToggle: () => void;
}

interface SearchEntry {
  title: string;
  path: string;
  section: string;
  headings: string[];
}

export function Header({ onMenuToggle }: HeaderProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen(true);
        const input = document.querySelector('.header__search-input') as HTMLInputElement | null;
        input?.focus();
      }
      if (e.key === 'Escape') {
        setOpen(false);
        setQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const results = useMemo(() => {
    if (query.trim().length < 2) return [];
    const lower = query.toLowerCase();
    return (searchIndex as SearchEntry[])
      .filter((item) => {
        const inTitle = item.title.toLowerCase().includes(lower);
        const inSection = item.section.toLowerCase().includes(lower);
        const inHeading = item.headings.some((heading) => heading.toLowerCase().includes(lower));
        return inTitle || inSection || inHeading;
      })
      .slice(0, 8);
  }, [query]);

  return (
    <header className="header">
      <div className="header__left">
        <button className="header__menu-btn" onClick={onMenuToggle} aria-label={zh.header.openMenuAria}>
          <span />
          <span />
          <span />
        </button>
        <Link to="/" className="header__brand">
          <img
            className="header__brand-logo"
            src={`${import.meta.env.BASE_URL}favicon.svg`}
            alt=""
            width={28}
            height={28}
            decoding="async"
            draggable={false}
          />
          <span className="header__brand-text">
            {zh.common.brandName} {zh.common.docsSuffix}
          </span>
        </Link>
      </div>

      <div className="header__search-shell" ref={ref}>
        <div className="header__search">
          <svg className="header__search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M11 11l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            className="header__search-input"
            placeholder={zh.header.searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setOpen(true)}
          />
          <kbd className="header__search-kbd">⌘K</kbd>
        </div>

        {open && query.trim().length >= 2 && (
          <div className="header__search-dropdown" role="listbox" aria-label={zh.header.searchPlaceholder}>
            {results.length > 0 ? (
              results.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="header__search-result"
                  role="option"
                  onClick={() => {
                    setOpen(false);
                    setQuery('');
                  }}
                >
                  <div className="header__search-copy">
                    <span className="header__search-title">{item.title}</span>
                    <span className="header__search-meta">{item.section}</span>
                  </div>
                  <span className="header__search-arrow">↗</span>
                </Link>
              ))
            ) : (
              <div className="header__search-empty" role="status">
                {zh.header.searchNoResults}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="header__right">
        <Link to="/docs/dev/development-log" className="header__changelog">
          {zh.header.changelogLink}
        </Link>
        {GITHUB_REPO_URL ? (
          <a href={GITHUB_REPO_URL} target="_blank" rel="noopener noreferrer" className="header__github">
            {zh.header.sourceLink}
          </a>
        ) : (
          <span className="header__github" title="未配置公开仓库地址（构建时未设置 VITE_GITHUB_REPO_URL）">
            {zh.header.sourceLink}
          </span>
        )}
      </div>
    </header>
  );
}
