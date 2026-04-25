import { Link } from 'react-router-dom';
import { GITHUB_REPO_URL } from '@/config/public';
import { ArrowUpRight, FileText } from 'lucide-react';
import { navConfig } from '@/utils/nav-config';
import zh from '@/locales/zh-CN.json';
import {
  audiencePathIcon,
  capabilityIcons,
  homeCtaIcons,
  homePanelIcons,
  homeTopNavIcons,
  sectionTitleIcon,
} from './home-page-icons';
import './HomePage.css';

const lucideSm = { className: 'home-page__lucide home-page__lucide--sm', size: 14, strokeWidth: 1.75 } as const;
const lucideMd = { className: 'home-page__lucide home-page__lucide--md', size: 18, strokeWidth: 1.75 } as const;
const lucideLg = { className: 'home-page__lucide home-page__lucide--lg', size: 20, strokeWidth: 1.75 } as const;
const lucideNav = { className: 'home-page__lucide', size: 16, strokeWidth: 1.75 } as const;
const lucideCta = { className: 'home-page__lucide', size: 16, strokeWidth: 1.75 } as const;

const {
  overview: NavOverviewIcon,
  quickStart: NavQuickIcon,
  developers: NavDevIcon,
  source: NavSourceIcon,
} = homeTopNavIcons;
const { primary: CtaPrimaryIcon, secondary: CtaSecondaryIcon } = homeCtaIcons;
const { capabilities: PanelCapIcon, audiences: PanelAudIcon } = homePanelIcons;

export function HomePage() {
  const { home: h, homeAudiences, homeCapabilities, common } = zh;
  const EyebrowIcon = PanelCapIcon;

  return (
    <div className="home-page">
      <header className="home-page__topbar">
        <div className="home-page__topbar-row">
          <Link to="/" className="home-page__brand">
            <span className="home-page__brand-copy">
              {common.brandName} {common.docsSuffix}
            </span>
          </Link>
          <nav className="home-page__topnav" aria-label="主导航">
            <Link to="/docs/overview">
              <NavOverviewIcon aria-hidden {...lucideNav} />
              {h.navOverview}
            </Link>
            <Link to="/docs/QUICK_START">
              <NavQuickIcon aria-hidden {...lucideNav} />
              {h.navQuickStart}
            </Link>
            <Link to="/docs/dev/architecture-overview">
              <NavDevIcon aria-hidden {...lucideNav} />
              {h.navDevelopers}
            </Link>
            {GITHUB_REPO_URL ? (
              <a href={GITHUB_REPO_URL} target="_blank" rel="noopener noreferrer">
                <NavSourceIcon aria-hidden {...lucideNav} />
                {h.navSource}
              </a>
            ) : (
              <span className="home-page__nav-fallback" title="未配置公开仓库地址">
                <NavSourceIcon aria-hidden {...lucideNav} />
                {h.navSource}
              </span>
            )}
          </nav>
        </div>
      </header>

      <main className="home-page__body">
        <section className="home-page__hero">
          <p className="home-page__eyebrow">
            <EyebrowIcon aria-hidden {...lucideSm} />
            {h.heroEyebrow}
          </p>
          <h1 className="home-page__title">{h.heroTitle}</h1>
          <p className="home-page__lead">{h.heroLead}</p>
          <div className="home-page__actions">
            <Link to="/docs/QUICK_START" className="home-page__action home-page__action--primary">
              <CtaPrimaryIcon aria-hidden {...lucideCta} />
              {h.actionPrimary}
            </Link>
            <Link to="/docs/overview" className="home-page__action">
              <CtaSecondaryIcon aria-hidden {...lucideCta} />
              {h.actionSecondary}
            </Link>
          </div>
        </section>

        <section className="home-page__grid">
          <div className="home-page__panel">
            <p className="home-page__panel-title">
              <PanelCapIcon aria-hidden {...lucideMd} />
              {h.panelCapabilities}
            </p>
            <ul className="home-page__cap-list">
              {homeCapabilities.map((item, i) => {
                const CapIcon = capabilityIcons[i] ?? FileText;
                return (
                  <li key={item} className="home-page__cap-item">
                    <span className="home-page__cap-icon" aria-hidden>
                      <CapIcon {...lucideSm} />
                    </span>
                    <span>{item}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="home-page__panel">
            <p className="home-page__panel-title">
              <PanelAudIcon aria-hidden {...lucideMd} />
              {h.panelStart}
            </p>
            <div className="home-page__link-list">
              {homeAudiences.map((item) => {
                const CardIcon = audiencePathIcon[item.path] ?? FileText;
                return (
                  <Link key={item.path} to={item.path} className="home-page__link-card">
                    <span className="home-page__link-card-pict" aria-hidden>
                      <CardIcon {...lucideLg} />
                    </span>
                    <div className="home-page__link-card-body">
                      <strong>{item.title}</strong>
                      <p>{item.description}</p>
                    </div>
                    <ArrowUpRight className="home-page__link-card-arrow" aria-hidden size={18} strokeWidth={1.75} />
                  </Link>
                );
              })}
            </div>
          </div>
        </section>

        <section className="home-page__sections">
          {navConfig
            .filter((section) => section.title !== h.excludeNavSection)
            .map((section) => {
              const SectionIcon = sectionTitleIcon[section.title] ?? FileText;
              return (
                <section key={section.title} className="home-page__section-block">
                  <div className="home-page__section-head">
                    <span className="home-page__section-kicker-icon" aria-hidden>
                      <SectionIcon {...lucideMd} />
                    </span>
                    <p className="home-page__section-kicker">{section.title}</p>
                  </div>
                  <div className="home-page__section-links">
                    {section.items.map((item) => (
                      <Link key={item.path} to={item.path} className="home-page__section-link">
                        <span>{item.title}</span>
                        <small>{item.label}</small>
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}
        </section>
      </main>
    </div>
  );
}
