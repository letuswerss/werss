import { defineNavSection, type NavSection } from './types';
import zh from '@/locales/zh-CN.json';

export const navConfig: NavSection[] = zh.nav.sections.map((s) => defineNavSection(s as NavSection));

export function findNavItem(path: string): { section: NavSection; item: NavSection['items'][0] } | null {
  for (const section of navConfig) {
    const item = section.items.find((i) => i.path === path);
    if (item) return { section, item };
  }
  return null;
}

export function getPrevNext(path: string): { prev: NavSection['items'][0] | null; next: NavSection['items'][0] | null } {
  const allItems = navConfig.flatMap((s) => s.items).filter((i) => i.path !== '/');
  const idx = allItems.findIndex((i) => i.path === path);
  return {
    prev: idx > 0 ? allItems[idx - 1]! : null,
    next: idx >= 0 && idx < allItems.length - 1 ? allItems[idx + 1]! : null,
  };
}
