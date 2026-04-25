export interface FetchTask {
  id: string
  name: string
  mps_id: string
  cron_exp: string
  max_page?: number | null
  status: number
  created_at: string
  updated_at: string
}

export interface FetchTaskCreate {
  name: string
  mps_id: string
  cron_exp: string
  max_page?: number | null
  status?: number
}
