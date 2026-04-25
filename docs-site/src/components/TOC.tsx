import { useEffect, useMemo, useState } from 'react';
import zh from '@/locales/zh-CN.json';
import './TOC.css';

interface TocItem {
  id: string;
  text: string;
  level: number;
}

interface TOCProps {
  content: string;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[`*_[\]()]/g, '')
    .replace(/[^\w\u4e00-\u9fa5\s-]/g, '')
    .replace(/\s+/g, '-');
}

function extractHeadings(markdown: string): TocItem[] {
  const headings: TocItem[] = [];
  const lines = markdown.split('\n');

  for (const line of lines) {
    const match = /^(##|###)\s+(.+)$/.exec(line.trim());
    if (!match) continue;

    const level = match[1].length;
    const text = match[2].trim();
    headings.push({
      id: slugify(text),
      text,
      level,
    });
  }

  return headings;
}

export function TOC({ content }: TOCProps) {
  const headings = useMemo(() => extractHeadings(content), [content]);
  const [activeId, setActiveId] = useState('');

  useEffect(() => {
    if (!headings.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting);
        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      { rootMargin: '-96px 0px -72% 0px' }
    );

    headings.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [headings]);

  if (!headings.length) return null;

  return (
    <aside className="toc">
      <p className="toc__eyebrow">{zh.toc.eyebrow}</p>
      <ul className="toc__list">
        {headings.map((h) => (
          <li key={h.id} className={`toc__item toc__item--level-${h.level}`}>
            <a href={`#${h.id}`} className={`toc__link ${activeId === h.id ? 'toc__link--active' : ''}`}>
              {h.text}
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
