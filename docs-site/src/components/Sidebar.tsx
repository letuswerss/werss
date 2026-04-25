import { Link, useLocation } from 'react-router-dom';
import { navConfig } from '@/utils/nav-config';
import zh from '@/locales/zh-CN.json';
import './Sidebar.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <>
      <aside className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar__inner">
          {navConfig.map((section) => {
            return (
              <section key={section.title} className="sidebar__section">
                <p className="sidebar__section-title">{section.title}</p>
                <ul className="sidebar__list">
                  {section.items.map((item) => {
                    const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(`${item.path}/`));
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`sidebar__link ${active ? 'sidebar__link--active' : ''}`}
                          onClick={onClose}
                        >
                          {item.title}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      </aside>
      <button
        className={`sidebar__overlay ${isOpen ? 'sidebar__overlay--visible' : ''}`}
        onClick={onClose}
        aria-label={zh.sidebar.closeOverlayAria}
      />
    </>
  );
}
