export interface NavItem {
  title: string;
  path: string;
  label: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export function defineNavSection(config: NavSection): NavSection {
  return config;
}
