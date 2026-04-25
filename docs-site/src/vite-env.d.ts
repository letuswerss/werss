/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 如 https://github.com/owner/repo ；不设则「源码」不指向外链 */
  readonly VITE_GITHUB_REPO_URL?: string
  /** 如 https://github.com/owner/repo/blob/main ；不设则库内相对链接不跳 GitHub */
  readonly VITE_GITHUB_BLOB_BASE?: string
}
