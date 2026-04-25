/** 将 `{name}` 占位符替换为 `vars[name]` */
export function interpolate(template: string, vars: Record<string, string>) {
  return template.replace(/\{(\w+)\}/g, (_m, key: string) => (key in vars ? vars[key]! : `{${key}}`));
}
