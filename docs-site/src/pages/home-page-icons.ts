import {
  type LucideIcon,
  BookOpen,
  Boxes,
  Brain,
  Code2,
  Compass,
  Github,
  Inbox,
  LayoutGrid,
  Library,
  Lightbulb,
  Rocket,
  Rss,
  Send,
  Sparkles,
  Tags,
  Terminal,
  TrendingUp,
  Users,
  Workflow,
  Zap,
} from 'lucide-react';

/** 按文档分区标题映射（与 zh-CN nav.sections.title 一致） */
export const sectionTitleIcon: Record<string, LucideIcon> = {
  理解系统: Lightbulb,
  核心功能: Boxes,
  功能与页面: LayoutGrid,
  开发文档: Code2,
  参考资料: Library,
};

/** 「按角色开始」各入口（按 homeAudiences.path） */
export const audiencePathIcon: Record<string, LucideIcon> = {
  '/docs/QUICK_START': Terminal,
  '/docs/concepts': Brain,
  '/docs/features/article-workbench': Workflow,
  '/docs/overview': Compass,
};

/** WeRSS 能做什么：与 homeCapabilities 顺序一一对应 */
export const capabilityIcons: LucideIcon[] = [Inbox, Rss, Tags, TrendingUp, Send];

export const homePanelIcons = {
  capabilities: Sparkles,
  audiences: Users,
} as const;

export const homeTopNavIcons = {
  overview: BookOpen,
  quickStart: Zap,
  developers: Code2,
  source: Github,
} as const;

export const homeCtaIcons = {
  primary: Rocket,
  secondary: BookOpen,
} as const;
