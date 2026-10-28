export const product = { name: 'TANPHAT ONE', mark: 'TP' } as const;

// Product names are independent of Odoo addon/model identifiers.
// Only link to a subsystem once its routes and access checks are available.
export const subsystems = {
  dashboard: { name: 'TP Dashboard', description: 'Điều hành doanh nghiệp' },
  projects: { name: 'TP Projects', description: 'Quản lý dự án cầu đường' },
  survey: { name: 'TP Survey', description: 'Quản lý khảo sát hiện trường' },
  design: { name: 'TP Design', description: 'Quản lý hồ sơ thiết kế' },
  contracts: { name: 'TP Contracts', description: 'Quản lý hợp đồng' },
  tasks: { name: 'TP Tasks', description: 'Quản lý tiến độ, giao việc' },
  hr: { name: 'TP HR', description: 'Quản lý nhân sự' },
  finance: { name: 'TP Finance', description: 'Quản lý tài chính, chi phí' },
  documents: { name: 'TP Documents', description: 'Quản lý văn bản, hồ sơ' },
} as const;
