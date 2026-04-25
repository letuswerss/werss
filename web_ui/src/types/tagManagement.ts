export interface Tag {
  id: string
  name: string
  cover?: string | null
  intro?: string | null
  status: number
  mps_id?: string | null
  is_custom?: boolean
  created_at: string
  updated_at: string
  article_count?: number  // 标签关联的文章数量（热度）
}

export interface TagCreate {
  name: string
  cover?: string | null
  intro?: string | null
  mps_id?: string | null
  status?: number
  is_custom?: boolean
}
