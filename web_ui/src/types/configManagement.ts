export interface ConfigManagement {
  config_key: string
  config_value: string
  description?: string
  created_at: string
  updated_at: string
}

export interface ConfigManagementCreate {
  config_key: string
  config_value: string
  description?: string
}

export interface ConfigManagementUpdate {
  config_value?: string
  description?: string
}