export interface NotifyTask {
  id: string
  name: string
  message_type: number
  message_template: string
  web_hook_url: string
  mps_id: string
  cron_exp: string
  status: number
  created_at: string
  updated_at: string
}

export interface NotifyTaskCreate {
  name: string
  message_type: number
  message_template: string
  web_hook_url: string
  mps_id: string
  cron_exp: string
  status?: number
}
